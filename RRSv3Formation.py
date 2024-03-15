# This script uses the RRSFormation class from RRSFormation.py to form RRSv3. RRSv3 involves sampling a fixed number of DMI instances per DMI type from PPIs randomized using all human proteins from SwissProt.
# Author: Chop Yan Lee

# For RRSv3 and 4, make sure to only sample from proteins with network information.
# For RRSv3, due to the sheer amount of possible combinations of the human proteome, I will group the proteins based on their domain matches (SLiM cognate domains) and their SLiM matches. Protein pairs will then be generated by pairing proteins from domain match groups and their corresponding SLiM groups.
# Select 4 instances per DMI type because after trying the code, I got around 282 DMI type matched in the human proteome with network info.

# import protein_interaction_interfaces
from DMIDB import *
import DMIDB
import RRSFormation
import sys, random, itertools

class InterfaceHandling(DMIDB.InterfaceHandling):
    """
    Inherits from DMIDB.InterfaceHandling

    Added a method to read in only proteins with network information

    Attributes:
        domain_groups (dict): Dict that binds SLiM-binding domains and the proteins having these domains. Keys are tuples of domains or combinations of domains that are known from DMI type list to bind to SLiM, and values are lists of UniProt IDs that possess the domains or combinations of domains
        slim_groups (dict): Similar to domain_groups. Keys are slim ids (ELME000XX) and values are lists of UniProt IDs that have at least one match of the slim id.
    """
    def __init__(self, prot_path, slim_type_file, dmi_type_file, smart_domain_types_file, pfam_domain_types_file, smart_domain_matches_json_file, pfam_domain_matches_json_file, features_path, PPI_file= None, network_path= None):
        """
        Instantiate InterfaceHandling

        Args:
            domain_groups (dict): Dict that binds SLiM-binding domains and the proteins having these domains. Keys are tuples of domains or combinations of domains that are known from DMI type list to bind to SLiM, and values are lists of UniProt IDs that possess the domains or combinations of domains
            slim_groups (dict): Similar to domain_groups. Keys are slim ids (ELME000XX) and values are lists of UniProt IDs that have at least one match of the slim id.
        """
        super().__init__(prot_path, slim_type_file, dmi_type_file, smart_domain_types_file, pfam_domain_types_file, smart_domain_matches_json_file, pfam_domain_matches_json_file, features_path, PPI_file, network_path)
        self.domain_groups= {}
        self.slim_groups= {}

    def read_in_proteins_with_network(self):
        """
        Read into self.proteins_dict only the proteins with network information
        """
        proteins_with_networks= set()

        file_names= [file_name for file_name in glob.glob(InterfaceHandling.network_path + '/*')]
        for file_name in file_names:
            prot_file= file_name.split('/')[-1]
            prot_id= prot_file.split('_')[0]
            proteins_with_networks.add(prot_id)

        file_names= [file_name for file_name in glob.glob(self.prot_path + '/*')]
        for file_name in file_names:
            prot_file= file_name.split('/')[-1]
            prot_id, _ = prot_file.split('.')
            if prot_id in proteins_with_networks:
                with open(file_name,'r') as file:
                    lines = [line.strip() for line in file.readlines()]
                for line in lines:
                    if line[0] == '>':
                        protein_id= line[1:]
                        prot_inst= Protein(protein_id)
                        self.proteins_dict[protein_id]= prot_inst
                    else:
                        self.proteins_dict[protein_id].sequence = line
        print(f'{len(self.proteins_dict)} proteins read in.')

    def get_domain_groups(self):
        """
        Iterate over all DMI types to find the domains or domain combinations required to bind different SLiM types. The domains or domain combinations are saved as keys in a dictionary where proteins having matches or these domains or combinations of domains are stored in a list and saved as values in the dictionary. The dictionary is stored as self.domain_groups.
        """
        # set up the domain groups
        for dmi_type, dmi_type_inst in self.dmi_types_dict.items():
            if len(dmi_type_inst.domain_interfaces) > 1:
                for domain_interface in dmi_type_inst.domain_interfaces:
                    self.domain_groups[tuple(domain_interface.domain_dict.keys())]= [] # if binding requires two domains from two interactors, then they are treated as two tuples that become two different keys 
            else:
                self.domain_groups[tuple(dmi_type_inst.domain_interfaces[0].domain_dict.keys())]= [] # ('PF123') for one domain binding to one SLiM or ('PF123','PF321) for two domains from the interactor binding to one SLiM

        # add proteins with domain match into their respective group
        for prot, prot_inst in self.proteins_dict.items():
            if any(prot_inst.domain_matches_dict):
                for domain_match_id in prot_inst.domain_matches_dict:
                    if tuple([domain_match_id]) in self.domain_groups:
                        self.domain_groups[tuple([domain_match_id])].append(prot)
                for domain_group in self.domain_groups: # group proteins that have two domain interfaces
                    if len(domain_group) == 2:
                        if set(prot_inst.domain_matches_dict).intersection(set(domain_group)) == set(domain_group):
                            self.domain_groups[domain_group].append(prot)

    def get_slim_groups(self):
        """
        Iterate over all DMI types and set up a dictionary with SLiM IDs as keys. The proteins having matches of the SLiM types are stored in a list and saved as values in the dictionary. The dictionary is stored as self.slim_groups.
        """
        for dmi_type in self.dmi_types_dict:
            self.slim_groups[dmi_type]= []

        for prot, prot_inst in self.proteins_dict.items():
            if any(prot_inst.slim_matches_dict):
                for slim_id in prot_inst.slim_matches_dict:
                    self.slim_groups[slim_id].append(prot)

class RRSv3Formation(RRSFormation.RRSFormation):
    """
    Represents random reference set version 3

    Inherits from RRSFormation.RRSFormation
    """

    def __init__(self, RRS_version):
        """
        Instantiate RRS

        Args:
            RRS_version (str): a version name given to RRS, e.g. RRSv1_1_20210427 as RRS version 1, triplicate 1 and date of generating the RRS
        """
        super().__init__(RRS_version)

    def make_random_protein_pairs_with_groups_select_RRS_instances(self, number_instances):
        """
        Generate random protein pairs among the proteins saved in self.domain_groups and self.slim_groups. Sample a fixed number of RRS instances per DMI type.

        Args:
            number_instances (int): Number of RRS instances to be sampled for each DMI type
        """
        for slim_id, slim_prots in InterfaceHandling.slim_groups.items():
            InterfaceHandling.protein_pairs_dict= {}
            dmi_type_inst= InterfaceHandling.dmi_types_dict[slim_id]
            domains= []
            if len(dmi_type_inst.domain_interfaces) > 1:
                for domain_interface in dmi_type_inst.domain_interfaces:
                    domains.append(list(domain_interface.domain_dict)[0])
            else:
                domains.append(list(dmi_type_inst.domain_interfaces[0].domain_dict))
            for domain in domains:
                if type(domain) == str:
                    domain_prots= InterfaceHandling.domain_groups[tuple([domain])]
                else:
                    domain_prots= InterfaceHandling.domain_groups[tuple(domain)]
                if (any(domain_prots)) & (any(slim_prots)):
                    if len(list(itertools.product(domain_prots, slim_prots))) > 50:
                        random_protein_pair= random.sample(list(itertools.product(domain_prots, slim_prots)), 50)
                    else:
                        random_protein_pair= list(itertools.product(domain_prots, slim_prots))
                    for pp in random_protein_pair:
                        pp= tuple(sorted(pp))
                        if pp not in InterfaceHandling.known_PPIs:
                            InterfaceHandling.protein_pairs_dict[pp]= DMIDB.ProteinPair(pp[0], pp[1])
                    InterfaceHandling.find_DMI_matches()
                    if len(InterfaceHandling.protein_pairs_dict) >= number_instances: # if the regex is not strict and many random PPIs have random DMI matches, sample only a subset of random PPIs and restrict to one RRS instance sampled per random PPI
                        for protpair in random.sample(list(InterfaceHandling.protein_pairs_dict), number_instances):
                            self.RRS_instances= self.RRS_instances + random.sample(InterfaceHandling.protein_pairs_dict[protpair].dmi_matches_dict[slim_id], 1)
                    else: # if regex is strict and not many random PPIs are available for RRS instance sampling, use all random PPIs available to sample one RRS instance per random PPI
                        for protpair, protpair_inst in InterfaceHandling.protein_pairs_dict.items():
                            self.RRS_instances= self.RRS_instances + random.sample(protpair_inst.dmi_matches_dict[slim_id], 1)

if __name__ == '__main__':

    prot_path= sys.argv[1]
    PPI_file= sys.argv[2]
    slim_type_file= sys.argv[3]
    dmi_type_file= sys.argv[4]
    smart_domain_types_file= sys.argv[5]
    pfam_domain_types_file= sys.argv[6]
    smart_domain_matches_json_file= sys.argv[7]
    pfam_domain_matches_json_file= sys.argv[8]
    features_path= sys.argv[9]
    network_path= sys.argv[10]
    number_instances= int(sys.argv[11])
    RRS_version= list(sys.argv[12:])

    InterfaceHandling= InterfaceHandling(prot_path, slim_type_file, dmi_type_file, smart_domain_types_file, pfam_domain_types_file, smart_domain_matches_json_file, pfam_domain_matches_json_file, features_path, PPI_file= PPI_file, network_path= network_path)
    InterfaceHandling.read_in_proteins_with_network()
    InterfaceHandling.read_in_known_PPIs()
    InterfaceHandling.read_in_slim_types()
    InterfaceHandling.read_in_DMI_types()
    InterfaceHandling.read_in_domain_types()
    InterfaceHandling.read_in_domain_matches()
    InterfaceHandling.get_domain_groups()
    InterfaceHandling.create_slim_matches_all_proteins()
    InterfaceHandling.get_slim_groups()
    for RRS in RRS_version:
        RRSv3= RRSv3Formation(RRS)
        RRSv3.make_random_protein_pairs_with_groups_select_RRS_instances(number_instances)
        RRSv3.write_out_RRS_instances(InterfaceHandling)

    # python3 RRSv3Formation.py ~/Coding/Python/DMI/protein_sequences_and_features/human_protein_sequences PRS_hi_lit17_IntAct_known_PPIs_20210427.txt ../elm_classes_20210222.tsv ../elm_interaction_domains_complete_20210222.tsv ../domain_stuffs/all_smart_domains_with_frequency.txt ../domain_stuffs/all_pfam_domains_with_frequency.txt ../domain_stuffs/interpro_9606_smart_matches_20210122.json ../domain_stuffs/interpro_9606_pfam_matches_20210122.json ../protein_sequences_and_features/human_protein_sequences_features ../protein_sequences_and_features/human_protein_sequences_features/Protein_networks_PRS_filtered 4 RRSv3_1_20210428 RRSv3_2_20210428 RRSv3_3_20210428
