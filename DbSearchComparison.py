#!/usr/bin/python3
import sys
import datetime
import re
import pandas
import getopt
import os

"""
Short script to compare the PEAKS psm search output to find overlap and distinction between the matched peptides.
"""


def clean_peptide_col(peptide_column):
    """Cleans up the peptide column by removing unnecessary information and returns the peptide"""
    sample_line = "K.ELC(+57.02)EQ(+.98)EC(+57.02)EWEEITITGSDGSTR.V"
    no_parentheses_pep = re.sub(r'\([^()]*\)', '', peptide_column)
    stripped_pep = no_parentheses_pep.replace('.', '')
    return stripped_pep


def extract_csv_data(input_file):
    """Reads PEAKS protein-peptide.csv file as dataframe to extract unique peptides and matching ORF accessions"""
    csv_data = pandas.read_csv(input_file, header='infer', delimiter=',')
    for i, row in csv_data.iterrows():
        raw_peptide = csv_data.at[i, 'Peptide']
        csv_data.at[i, 'Peptide'] = clean_peptide_col(raw_peptide)
    csv_data = csv_data.drop_duplicates(subset=['Protein Accession', 'Peptide'], keep='first')
    return csv_data


def find_distinct_peptides(transdecoder_data, genemark_data, prefix):
    """Filters the CSV files so only distinct peptides remain"""
    distinct_td_csv = "comparison_output/{}_distinct_td.csv".format(prefix)
    distinct_gm_csv = "comparison_output/{}_distinct_gm.csv".format(prefix)
    with open(distinct_td_csv, "w+") as distinct_transdecoder, \
            open(distinct_gm_csv, "w+") as distinct_genemark:
        td_merged = pandas.merge(transdecoder_data, genemark_data, on='Peptide', how='left', indicator=True) \
            .query("_merge == 'left_only'")
        gm_merged = pandas.merge(transdecoder_data, genemark_data, on='Peptide', how='right', indicator=True) \
            .query("_merge == 'right_only'")
        td_merged[['Protein Accession_x', 'Peptide']] \
            .to_csv(distinct_transdecoder, sep=',', mode='w', index=False, header=['Protein Accession', 'Peptide'])
        gm_merged[['Protein Accession_y', 'Peptide']] \
            .to_csv(distinct_genemark, sep=',', mode='w', index=False, header=['Protein Accession', 'Peptide'])


def main(argv):
    genemark_csv = ''
    transdecoder_csv = ''
    output_prefix = ''

    try:
        opts, args = getopt.getopt(argv, 'g:t:p:', ['genemark=', 'transdecoder=', 'prefix='])
    except getopt.GetoptError:
        print("usage: DbSearchComparison.py -g <genemark csv file> -t <transdecoder csv file> -p <output prefix>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-g', '--genemark'):
            genemark_csv = arg
        elif opt in ('-t', '--transdecoder'):
            transdecoder_csv = arg
        elif opt in ('-p', '--prefix'):
            output_prefix = arg
        else:
            print("usage: DbSearchComparison.py -g <genemark csv file> -t <transdecoder  csv file> -p <output prefix>")
            sys.exit(2)

    try:
        os.makedirs("comparison_output")
    except FileExistsError:
        pass

    genemark_data = extract_csv_data(genemark_csv)
    transdecoder_data = extract_csv_data(transdecoder_csv)

    find_distinct_peptides(transdecoder_data, genemark_data, output_prefix)


if __name__ == '__main__':
    main(sys.argv[1:])
