#!/usr/bin/python3
"""
-g data/propep_genemark_decoy.csv -t data/propep_transdecoder_decoy.csv -p test1
"""

import datetime
import getopt
import os
import re
import sys

import pandas
from matplotlib import pyplot as plt
from matplotlib_venn import venn2


def clean_peptide_col(peptide_column):
    """Cleans up the peptide column by removing unnecessary information and returns the peptide"""
    no_parentheses_pep = re.sub(r'\([^()]*\)', '', peptide_column)
    stripped_pep = no_parentheses_pep.replace('.', '')
    return stripped_pep


def extract_csv_data(input_file):
    csv_data = pandas.read_csv(input_file, header='infer', delimiter=',')
    for i, row in csv_data.iterrows():
        raw_peptide = csv_data.at[i, 'Peptide']
        csv_data.at[i, 'Peptide'] = clean_peptide_col(raw_peptide)
    csv_data = csv_data[['Protein Accession', 'Peptide']].drop_duplicates(subset=['Peptide'], keep='first')
    print(len(csv_data))
    return csv_data


def find_distinct_peptides(decoy_transdecoder, decoy_genemark, transdecoder, genemark, prefix):
    """Filters the CSV files so only distinct peptides remain"""

    td_merged = pandas.merge(decoy_transdecoder, decoy_genemark, on='Peptide', how='left', indicator=True) \
        .query("_merge == 'left_only'")
    gm_merged = pandas.merge(decoy_transdecoder, decoy_genemark, on='Peptide', how='right', indicator=True) \
        .query("_merge == 'right_only'")

    overlap_merge = pandas.merge(decoy_transdecoder, decoy_genemark, on='Peptide', how='inner', indicator=True) \
        .query("_merge == 'both'")
    print(len(overlap_merge.index))
    print(len(td_merged.index))
    print(len(gm_merged.index))
    # with open("comparison_output/test_distinct_gm.csv", "w+") as distinct_genemark:
    #     gm_merged[['Protein Accession_y', 'Peptide']] \
    #         .to_csv(distinct_genemark, sep=',', mode='w', line_terminator='\n',
    #                 index=False, header=['Protein Accession', 'Peptide'])
    list_td_decoy = set(decoy_genemark.Peptide)
    list_gm_decoy = set(decoy_transdecoder.Peptide)
    list_td = set(transdecoder.Peptide)
    list_gm = set(genemark.Peptide)

    fig, axes = plt.subplots(nrows=2, ncols=2)
    # total_v1 = len(list_td.union(list_gm))
    # v1 = venn2([list_td, list_gm], set_labels=('Transdecoder', 'GenemarkS-T'), ax=axes[0][0],
    #            subset_label_formatter=lambda x: f"{(x/total_v1):1.0%}")
    v1 = venn2([list_td, list_gm], set_labels=('Transdecoder', 'GenemarkS-T'), ax=axes[0][0])
    v2 = venn2([list_td_decoy, list_gm_decoy], set_labels=('Transdecoder decoy', 'GenemarkS-T decoy'), ax=axes[0][1])
    v3 = venn2([list_td, list_td_decoy], set_labels=('Transdecoder', 'Transdecoder decoy'), ax=axes[1][0])
    v4 = venn2([list_gm, list_gm_decoy], set_labels=('GenemarkS-T', 'GenemarkS-T decoy'), ax=axes[1][1])

    plt.suptitle('Sample 01 peptide matches')
    plt.subplots_adjust(wspace=0.5, hspace=0.5)
    plt.tight_layout()
    plt.savefig('sample_{}.png'.format(prefix))


# decoy_genemark_file = "data/propep_genemark_decoy.csv"
# decoy_trans_file = "data/propep_transdecoder_decoy.csv"
# real_genemark_file = "data/propep_genemark_real.csv"
# real_trans_file = "data/propep_transdecoder_real.csv"


def main(argv):
    print(' '.join(argv))
    real_genemark_file = ''
    real_trans_file = ''
    decoy_genemark_file = ''
    decoy_trans_file = ''
    output_prefix = ''

    try:
        opts, args = getopt.getopt(argv[1:], 'g:t:h:u:p:', ['genemark=', 'transdecoder=',
                                                            'genemark_decoy=', 'transdecoder_decoy=', 'prefix='])
    except getopt.GetoptError:
        print("usage: db_search_comparison.py -g <genemark csv file> -t <transdecoder csv file> -p <output prefix>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-g', '--genemark'):
            real_genemark_file = arg
        elif opt in ('-t', '--transdecoder'):
            real_trans_file = arg
        elif opt in ('-h', '--genemark_decoy'):
            decoy_genemark_file = arg
        elif opt in ('-u', '--transdecoder_decoy'):
            decoy_trans_file = arg
        elif opt in ('-p', '--prefix'):
            output_prefix = arg
        else:
            print(
                "usage: db_search_comparison.py -g <genemark csv file> -t <transdecoder  csv file> -p <output prefix>")
            sys.exit(2)

    try:
        os.makedirs("comparison_output")
    except FileExistsError:
        pass

    print("started at: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    decoy_trans_data = extract_csv_data(decoy_trans_file)
    decoy_genemark_data = extract_csv_data(decoy_genemark_file)
    real_trans_data = extract_csv_data(real_trans_file)
    real_genemark_data = extract_csv_data(real_genemark_file)

    find_distinct_peptides(decoy_trans_data, decoy_genemark_data, real_trans_data, real_genemark_data, output_prefix)
    print("finished at: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))


if __name__ == '__main__':
    main(sys.argv)