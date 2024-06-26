# This script automates the exploratory analysis of the PRS and the combined replicates of different version of RRS.
# Author: Chop Yan Lee

import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

all_features= ['Probability', 'IUPredShort', 'Anchor', 'DomainOverlap', 'qfo_RLC', 'qfo_RLCvar', 'vertebrates_RLC', 'vertebrates_RLCvar', 'mammalia_RLC', 'mammalia_RLCvar', 'metazoa_RLC', 'metazoa_RLCvar', 'DomainEnrichment_pvalue', 'DomainEnrichment_zscore', 'DomainFreqbyProtein1', 'DomainFreqinProteome1']
all_columns= ['Accession', 'Elm', 'Regex', 'Pattern', 'Probability', 'interactorElm', 'ElmMatch', 'IUPredShort', 'Anchor', 'DomainOverlap', 'qfo_RLC', 'qfo_RLCvar', 'vertebrates_RLC', 'vertebrates_RLCvar', 'mammalia_RLC', 'mammalia_RLCvar', 'metazoa_RLC', 'metazoa_RLCvar', 'DomainEnrichment_pvalue', 'DomainEnrichment_zscore', 'TotalNetworkDegree', 'vertex_with_domain_in_real_network', 'interactorDomain', 'DomainID1', 'DomainMatch1', 'DomainMatchEvalue1', 'DomainFreqbyProtein1', 'DomainFreqinProteome1', 'DomainID2', 'DomainMatch2', 'DomainMatchEvalue2', 'DomainFreqbyProtein2', 'DomainFreqinProteome2', 'DMISource']

DMI_count_df= pd.DataFrame(data= {'Class': ['CLV', 'DEG', 'DOC', 'LIG', 'MOD', 'TRG'], 'ElmDB': [11, 25, 31, 165, 37, 22]})

fontsize= 12
title_fontsize= 14
sns.set_style('darkgrid')

def preprocessing_dataset(input):
    """
    Preprocess the NaNs and dummy values in the PRS and RRS. Rows with NaN are removed. Dummy value (88888) is replaced with the median of the feature in the dataset, i.e. median of the feature in PRS or median in RRS. All RRS replicates of an RRS versions are concatenated into one single RRS dataframe.
    
    Args:
        input (str or list of str): Absolute path to the PRS dataset or a list containing the absolute paths to the replicates of an RRS version

    Returns:
        df (pd.DataFrame): The processed dataframe
    """
    if type(input) == list:
        df= pd.DataFrame(columns= all_columns)
        for RRS in input:
            temp= pd.read_csv(RRS, sep= '\t', index_col= 0)
            temp.replace(88888, df.DomainEnrichment_zscore.median(), inplace= True)
            df= pd.concat([df, temp], axis= 0)
    else:
        df= pd.read_csv(input, sep= '\t', index_col= 0)
    for ind, row in df.iterrows():
        if pd.notna(row['DomainFreqbyProtein2']):
            df.loc[ind, 'DomainFreqbyProtein1'] = np.mean([row['DomainFreqbyProtein1'], row['DomainFreqbyProtein2']])
            df.loc[ind, 'DomainFreqinProteome1'] = np.mean([row['DomainFreqinProteome1'], row['DomainFreqinProteome2']])
    df.dropna(subset= all_features, inplace= True)
    df.rename(columns= {'DomainFreqbyProtein1': 'DomainFreqbyProtein', 'DomainFreqinProteome1': 'DomainFreqinProteome'}, inplace= True)
    return df

def make_DMI_fraction_plot(PRS_RRSvs_list):
    """
    Plot the representation of the DMI types in each ELM classes (DEG, DOC, etc.) in the PRS and RRS using the fraction of DMI type in each ELM classes. The plot is saved as pdf file.

    Args:
        PRS_RRSvs_list (list of pd.DataFrame): The processed PRS and RRS replicates from the function preprocessing_dataset. Note: the preprocessed PRS must be the first dataframe in the list
    """
    global DMI_count_df
    for i, df in enumerate(PRS_RRSvs_list):
        if i == 0:
            temp= pd.DataFrame(data= {'Class': pd.Series(df.Elm.unique()).str.slice(stop= 3).value_counts().index, 'PRS': pd.Series(df.Elm.unique()).str.slice(stop= 3).value_counts().values})
        else:
            temp= pd.DataFrame(data= {'Class': pd.Series(df.Elm.unique()).str.slice(stop= 3).value_counts().index, f'RRSv{i}': pd.Series(df.Elm.unique()).str.slice(stop= 3).value_counts().values})
        DMI_count_df= DMI_count_df.merge(temp, how= 'inner')
    for col in DMI_count_df.columns[1:]:
        DMI_count_df[f'{col}_fraction']= DMI_count_df[col]/DMI_count_df['ElmDB']

    N= 6
    ind= np.arange(N)
    width= 0.15
    color= sns.color_palette('deep')

    plt.figure(figsize= (8,6))
    for i, ele in enumerate(zip(color, DMI_count_df.columns[-5:])):
        c, col= ele
        plt.bar(ind + int(i)*width, DMI_count_df[col], width, color= c, label= col)

    plt.xticks(ind + 2*width, DMI_count_df.Class)
    plt.title(f'Fraction of DMI type represented in the PRS and RRSv1,2,3,4 by class', fontsize= title_fontsize)
    plt.ylabel('Fraction of DMI types with DMI instance', fontsize= fontsize)
    plt.legend(bbox_to_anchor= (1.05, 1), loc= 'upper left', borderaxespad= 0.)
    plt.ylim([0, 1.05])
    plt.savefig(plot_path + f'/DMI_fraction_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'DMI fraction plot of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

def make_feature_violin_plots(PRS_RRSvs_list):
    """
    Plot the distribution of different features in the PRS and RRS using violinplots. The plots are saved as pdf file.

    Args:
        PRS_RRSvs_list (list of pd.DataFrame): The processed PRS and RRS replicates from the function preprocessing_dataset. Note: the preprocessed PRS must be the first dataframe in the list
    """
    plt.figure(figsize= (6,6))
    plt.violinplot([-np.log10(df['Probability']) for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'SLiM probabibility distribution in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('SLiM Probability in -log10', fontsize= fontsize)
    plt.ylim([0, 16])
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/slim_probability_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'SLiM probability vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

    plt.figure(figsize= (6,6))
    plt.violinplot([df['DomainFreqbyProtein'] for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'Domain frequency distribution counted by protein in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('Domain frequency counted by protein', fontsize= fontsize)
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/Domainfreqbyprotein_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'DomainFreqbyProtein vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

    plt.figure(figsize= (6,6))
    plt.violinplot([df['DomainFreqinProteome'] for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'Domain frequency distribution in human proteome in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('Domain frequency in human proteome', fontsize= fontsize)
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/Domainfreqinproteome_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'DomainFreqinProteome vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

    plt.figure(figsize= (6,6))
    plt.violinplot([df['IUPredShort'] for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'IUPredShort distribution in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('IUPredShort scores', fontsize= fontsize)
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/IUPredShort_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'IUPredShort vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

    plt.figure(figsize= (6,6))
    plt.violinplot([df['metazoa_RLC'] for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'metazoa_RLC distribution in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('metazoa_RLC', fontsize= fontsize)
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/metazoa_RLC_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'metazoa_RLC vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

    plt.figure(figsize= (6,6))
    plt.violinplot([df['vertebrates_RLC'] for df in PRS_RRSvs_list], showmedians= True, widths= 0.8)
    plt.xticks([i + 1 for i in range(len(PRS_RRSvs_list))], ['PRS', 'RRSv1', 'RRSv2', 'RRSv3', 'RRSv4'])
    plt.title(f'vertebrates_RLC distribution in PRS and RRSv1,2,3,4', fontsize= title_fontsize)
    plt.ylabel('vertebrates_RLC', fontsize= fontsize)
    # plt.grid(alpha= 0.2)
    plt.savefig(plot_path + f'/vertebrates_RLC_vp_PRS_RRSv1_2_3_4.pdf', bbox_inches= 'tight')
    print(f'vertebrates_RLC vp of PRS and RRSv1_2_3_4 saved in {plot_path}.')
    plt.close()

if __name__ == '__main__':
    PRS= sys.argv[1]
    RRSv1_list= list(sys.argv[2:5])
    RRSv2_list= list(sys.argv[5:8])
    RRSv3_list= list(sys.argv[8:11])
    RRSv4_list= list(sys.argv[11:14])
    plot_path= '/'.join(sys.argv[2].split('/')[:2]) + '/Plots'
    print(plot_path)

    PRS= preprocessing_dataset(PRS)
    RRSv1= preprocessing_dataset(RRSv1_list)
    RRSv2= preprocessing_dataset(RRSv2_list)
    RRSv3= preprocessing_dataset(RRSv3_list)
    RRSv4= preprocessing_dataset(RRSv4_list)
    PRS_RRSvs_list= [PRS, RRSv1, RRSv2, RRSv3, RRSv4]
    make_DMI_fraction_plot(PRS_RRSvs_list)
    make_feature_violin_plots(PRS_RRSvs_list)

    # python3 feature_analysis_plots_between_RRSv.py ../PRS/PRS_v3_only_human_with_pattern_alt_iso_swapped_removed_20210413_slim_domain_features_annotated.tsv ../RRS/RRSv1/RRSv1_1_20210427_slim_domain_features_annotated.tsv ../RRS/RRSv1/RRSv1_2_20210427_slim_domain_features_annotated.tsv ../RRS/RRSv1/RRSv1_3_20210427_slim_domain_features_annotated.tsv ../RRS/RRSv2/RRSv2_1_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv2/RRSv2_2_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv2/RRSv2_3_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv3/RRSv3_1_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv3/RRSv3_2_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv3/RRSv3_3_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv4/RRSv4_1_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv4/RRSv4_2_20210428_slim_domain_features_annotated.tsv ../RRS/RRSv4/RRSv4_3_20210428_slim_domain_features_annotated.tsv
