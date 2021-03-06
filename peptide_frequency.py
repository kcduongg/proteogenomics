#!/usr/bin/python3
"""
A python module that counts and compares peptide frequency between two groups. Results can be found in a separate
output file.
Contains a Mann-Whitney U test
"""
import argparse
import datetime
import os
import sys

import pandas as pd
import scipy.stats as stats
import statsmodels.stats.multitest as sm

import csv_dataframe


def count_peptide_frequency(peptide_data, column_name):
    """Counts amount of PSMs per peptide"""
    count = pd.DataFrame(peptide_data['Peptide'].value_counts().reset_index())
    count.columns = ['Peptide', column_name]
    return count


def parts_per_million(data):
    """Converts dataframe values to parts per million across the columns"""
    data_sum = data.sum()
    ppm = data / data_sum * 1000000
    return ppm


def create_peptide_list(left_file, right_file):
    """Creates a list of all peptides as a DataFrame column"""
    joined_left = csv_dataframe.join_dataframes(left_file)
    joined_right = csv_dataframe.join_dataframes(right_file)
    all_peptides = joined_left.append(joined_right, ignore_index=True) \
        .drop_duplicates(subset=['Peptide'], keep='first').reset_index(drop=True)
    return all_peptides


def create_counter_dataframe(files, group_name, directory, all_peptides):
    """Creates full dataframe with peptide frequency in each sample"""
    output_file = "output/{}/peptide_count/peptide_frequency_{}.csv".format(directory, group_name)
    with open(files, "r") as file_list:
        for num, file in enumerate(file_list):
            file_data = csv_dataframe.extract_csv_data(file.strip(), drop_dupes=False)
            counter_column = count_peptide_frequency(file_data, "{}{}".format(group_name, num + 1))
            all_peptides = pd.merge(all_peptides, counter_column, on='Peptide', how='outer')

    all_peptides = all_peptides.fillna(0, downcast='infer')

    # # Normalising to ppm
    # for column in all_peptides.columns[1:]:
    #     all_peptides[column] = parts_per_million(all_peptides[column])

    with open(output_file, "w+") as output_file:
        all_peptides.to_csv(output_file, sep=',', mode='w', line_terminator='\n', index=False)
    return all_peptides


def mann_whitney_u_test(left_data, right_data, directory):
    peptides = left_data[['Peptide']].copy()
    for i, row in left_data.iterrows():
        left = left_data.iloc[i, 1:].tolist()
        right = right_data.iloc[i, 1:].tolist()
        if all(sample == left[0] for sample in left + right):
            continue
        u_statistic, p_value = stats.mannwhitneyu(left, right, alternative='two-sided')
        peptides.at[i, 'p-value'] = p_value
        peptides.at[i, 'u-statistic'] = u_statistic
    peptides = peptides.sort_values(by=['p-value'], ascending=True)
    with open("output/{}_mann_peptides.csv".format(directory), "w+") as output:
        peptides.to_csv(output, sep=',', mode='w', line_terminator='\n')
    return peptides


def multiple_test_correction(peptide_data, directory):
    p_values = peptide_data['p-value'].tolist()
    fdr_correction = sm.multipletests(p_values, alpha=0.05, method='fdr_bh', is_sorted=True)
    peptide_data['p_adjusted'] = fdr_correction[1]
    with open("output/{}_benj_peptides.csv".format(directory), "w+") as output:
        peptide_data.to_csv(output, sep=',', mode='w', line_terminator='\n')


def main(argv):
    print(' '.join(argv))
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-l', '--left', action='store', dest="left",
                        help="Specify the .txt file containing the first group of peptide .csv file paths",
                        required=True)
    parser.add_argument('-r', '--right', action='store', dest="right",
                        help="Specify the .txt file containing the second group of peptide .csv file paths",
                        required=True)
    parser.add_argument('--left_name', action='store', dest="left_name", default="left",
                        help="Name the left sample")
    parser.add_argument('--right_name', action='store', dest="right_name", default="right",
                        help="Name the right sample")
    parser.add_argument('-o', '--outdir', action='store', dest='outdir', default="peptides",
                        help="Provide an output directory name, i.e. 'output/<NAME>/peptide_count/'")
    args = parser.parse_args()

    try:
        os.makedirs("output/{}".format(args.outdir))
    except FileExistsError:
        pass
    try:
        os.makedirs("output/{}/peptide_count".format(args.outdir))
    except FileExistsError:
        pass

    try:
        print("Started at: " + datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        peptides = create_peptide_list(args.left, args.right)
        create_counter_dataframe(args.left, args.left_name, args.outdir, peptides)
        create_counter_dataframe(args.right, args.right_name, args.outdir, peptides)

        print("Finished at: " + datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    except FileNotFoundError as e:
        print(__doc__)
        print("Please provide valid files:")
        print(e)
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv)
