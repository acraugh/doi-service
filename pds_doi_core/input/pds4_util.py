import requests
from datetime import datetime
from enum import Enum

from pds_doi_core.input.exceptions import InputFormatException
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.entities.doi import Doi
logger = get_logger('pds_doi_core.input.pds4_util')

class BestParserMethod(Enum):
    BY_COMMA      = 1
    BY_SEMI_COLON = 2

class DOIPDS4LabelUtil:

    def get_doi_fields_from_pds4(self, xml_tree):
        pds4_fields = self.read_pds4(xml_tree)
        doi_fields = self.process_pds4_fields(pds4_fields)
        return doi_fields

    def read_pds4(self, xml_tree):
        """

        :param xml_tree: lxml etree
        :return:
        """
        pds4_field_value_dict = {}

        pds4_namespace = {'pds4': 'http://pds.nasa.gov/pds4/pds/v1'}
        xpath_dict = {
            'lid': '/*/pds4:Identification_Area/pds4:logical_identifier',
            'vid': '/*/pds4:Identification_Area/pds4:version_id',
            'title': '/*/pds4:Identification_Area/pds4:title',
            'publication_year':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:publication_year',
            'modification_date':
                '/*/pds4:Identification_Area/pds4:Modification_History/pds4:Modification_Detail/pds4:modification_date',
            'description': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:description',
            'product_class': '/*/pds4:Identification_Area/pds4:product_class',
            'authors': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:author_list',
            'editors': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:editor_list',
            # Desire only the 'name' field
            'investigation_area': '/*/pds4:Context_Area/pds4:Investigation_Area/pds4:name',
            # Desire only the 'name' field.
            'observing_system_component':
                '/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/pds4:name',
            # Desire only the 'name' field
            'target_identication': '/*/pds4:Context_Area/pds4:Target_Identification/pds4:name',
            'primary_result_summary':  '/pds4:Product_Bundle/pds4:Context_Area/pds4:Primary_Result_Summary/*',

        }

        for key, xpath in xpath_dict.items():
            elmts = xml_tree.xpath(xpath, namespaces=pds4_namespace)
            if elmts:
                pds4_field_value_dict[key] = ' '.join([elmt.text.strip() for elmt in elmts]).strip()

        return pds4_field_value_dict

    def _check_for_possible_full_name(self,names_list):
        # Given this list of token splitted using comma:
        # Case 1: "R. Deen, H. Abarca, P. Zamani, J.Maki"
        # determine if each token can be potentially a person' name: "R. Deen", "H. Abarca", "J.Maki"
        # This happens very rarely but it does happen.
        # Case 4 :"VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"

        o_list_contains_full_name_flag = False
        num_dots_found = 0
        num_person_names = 0

        for one_name in names_list:
            if '.' in one_name:
                num_dots_found += 1
                # Now that the dot is found, look to see the name contains at least two tokens.
                if len(one_name.strip().split('.')) >= 2:  # 'R. Deen' split to ['R','Deen'], "J.Maki" split to ['J','Maki']
                    num_person_names += 1
            else:
                # The name does not contain a dot, split using spaces.
                #  "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team" # Case 4  --> Should be parsed by semi-colon
                # A person's name should contain at least two tokens.
                if len(one_name.strip().split()) >= 2:
                    num_person_names += 1

        # If every name contains a dot, the list can potentially hold a person's name.
        # This does not work if the convention is broken of have the dot in each person's names.
        if num_dots_found == len(names_list) or num_person_names == len(names_list):
            o_list_contains_full_name_flag = True

        logger.debug(f"num_dots_found,num_person_names,len(names_list),names_list {num_dots_found,num_person_names,len(names_list),names_list}")
        logger.debug(f"o_list_contains_full_name_flag {o_list_contains_full_name_flag,names_list,len(names_list)}")

        return o_list_contains_full_name_flag
       
    # This next function will make a best guess as to which method is correct.
    # Examples of cases:
    #     pds4_fields_authors = "Lemmon, M."  # Case 1 --> Should be parsed by semi-colon
    #     pds4_fields_authors = "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team" # Case 4  --> Should be parsed by semi-colon
    #     pds4_fields_authors = "R. Deen, H. Abarca, P. Zamani, J.Maki" # Case 2 --> Should be parsed by comma
    #     pds4_fields_authors = "Davies, A.; Veeder, G."                # Case 3 --> Should be parsed by semi-colon
    #     pds4_fields_authors = "MER Science Team"  # Case 5 --> Should be parsed by semi-colon

    def _make_best_guess_method_to_parse_authors(self,pds4_fields_authors):
        # The 'authors' field from data provider is inconsistent.  Sometimes it is using comma ',' to separate
        # the names, sometimes it is using semi-colon ';'
        # This function will make a best guess as to which method is correct.

        o_best_method = None 
         
        authors_from_comma_split      = pds4_fields_authors.split(',')
        authors_from_semi_colon_split = pds4_fields_authors.split(';')

        # Check from authors_from_comma_split to see if it possibly contains full name.
        # Mostly this case: "R. Deen, H. Abarca, P. Zamani, J.Maki" # Case 2 --> Should be parsed by comma
        # When it is not obvious because it looks very similiar to this case:
        # "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team" # Case 4 --> Should be parsed by semi-colon

        list_from_comma_parsed_containing_full_name_flag = self._check_for_possible_full_name(authors_from_comma_split)

        number_commas      = pds4_fields_authors.count(',')
        number_semi_colons = pds4_fields_authors.count(';')

        if number_semi_colons == 0:
            if number_commas >= 1:
                if list_from_comma_parsed_containing_full_name_flag:
                    # Case 2: <author_list>R. Deen, H. Abarca, P. Zamani, J.Maki</author_list> 
                    o_best_method = BestParserMethod.BY_COMMA
                else:
                    # Case 1:  <author_list>Lemmon, M.</author_list>
                    # Case 4:  <author_list>VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team</author_list>
                    #          Only "VanBommel, S. J." will be considered as valid names to parse from.
                    o_best_method = BestParserMethod.BY_SEMI_COLON
            else:
                # Case 5: "MER Science Team"
                o_best_method = BestParserMethod.BY_SEMI_COLON
        else:
            # Case 3: <author_list>Davies, A.; Veeder, G.</author_list>
            o_best_method = BestParserMethod.BY_SEMI_COLON

        logger.debug(f"o_best_method,pds4_fields_authors {o_best_method,pds4_fields_authors} number_commas,number_semi_colons {number_commas,number_semi_colons}")
        logger.debug(f"len(authors_from_comma_split),len(authors_from_semi_colon_split) {len(authors_from_comma_split),len(authors_from_semi_colon_split)}")
        return o_best_method

    def process_pds4_fields(self, pds4_fields):
        doi_field_value_dict = {}

        product_type = pds4_fields['product_class'].split('_')[1]
        landing_page_template = 'https://pds.jpl.nasa.gov/ds-view/pds/view{}.jsp?identifier={}&version={}'

        site_url = landing_page_template.format(product_type,
                                                requests.utils.quote(pds4_fields['lid']),
                                                requests.utils.quote(pds4_fields['vid']))
        editors = self.get_editor_names(pds4_fields['editors'].split(';')) if 'editors' in pds4_fields.keys() else None

        # The 'authors' field is inconsistent on the use of separators.  Try to make a best guess on which method is better.
        o_best_method =  self._make_best_guess_method_to_parse_authors(pds4_fields['authors'])
        if o_best_method == BestParserMethod.BY_COMMA:
            authors_list = pds4_fields['authors'].split(',')
        elif o_best_method == BestParserMethod.BY_SEMI_COLON:
            authors_list = pds4_fields['authors'].split(';')
        else:
            logger.error(f"o_best_method,pds4_fields['authors'] {o_best_method,pds4_fields['authors']}")
            raise InputFormatException("Cannot split the authors using comma or semi-colon.")

        doi = Doi(title=pds4_fields['title'],
                  description=pds4_fields['description'],
                  publication_date=self.get_publication_date(pds4_fields),
                  product_type=product_type,
                  product_type_specific= "PDS4 Refereed Data " + product_type,
                  related_identifier=pds4_fields['lid'] + '::' + pds4_fields['vid'],
                  site_url=site_url,
                  authors=self.get_author_names(authors_list),
                  editors=editors,
                  keywords=self.get_keywords(pds4_fields),
                  date_record_added=self.get_record_added_date(pds4_fields)
                  )

        return doi

    def get_publication_date(self, pds4_fields):
        # The field 'modification_date' is favored first.  If it occurs, use it, otherwise use 'publication_year' field next.
        if 'modification_date' in pds4_fields.keys():
            logger.debug(f"pds4_fields['modification_date'] {pds4_fields['modification_date'],type(pds4_fields['modification_date'])}")
            # Some PDS4 label has more than one 'modification_date' fields so sort in ascending and select the first date.
            return datetime.strptime(sorted(pds4_fields['modification_date'].split(),reverse=False)[0], '%Y-%m-%d')
        elif 'publication_year' in pds4_fields.keys():
            return datetime.strptime(pds4_fields['publication_year'], '%Y')
        else:
            return datetime.now()

    def get_record_added_date(self, pds4_fields):
        # TO DO: have the creation date read from the transaction database if the record has been added earlier.

        return datetime.now().strftime('%Y-%m-%d')

    def get_keywords(self, pds4_fields):
        keyword_field = {'investigation_area', 'observing_system_component', 'target_identication', 'primary_result_summary'}
        keywords = set()
        for keyword_src in keyword_field:
            if keyword_src in pds4_fields.keys():
                keyword_list = [k.strip()
                                for k in pds4_fields[keyword_src].strip().split(" ") if len(k.strip()) > 0]
                keywords = keywords.union(keyword_list)

        # Take the fields as is as well without splitting on spaces
        if 'description' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['description'].lstrip().rstrip()])
        if 'investigation_area' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['investigation_area'].lstrip().rstrip()])
        # Example: 'IRTF 3.0-Meter Telescope'
        if 'observing_system_component' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['observing_system_component'].lstrip().rstrip()])

        # Remove words that may not be useful, such as 'of', 'or', 'the'.
        not_useful_words = ['of','or','the']
        for word_to_remove in not_useful_words:
            if word_to_remove in keywords:
                keywords.remove(word_to_remove)

        return keywords

    def _determine_need_to_swap_names_flag(self, split_full_name):
        # Given a list of names that has been split into individual components, determine if
        # the first and last name need to be swapped.
        # Cases: [' Bell III, J.F.']
        #        ['Joy, S. P.']
        o_need_to_swap_flag = False
        if ',' in split_full_name[0]:   #  ['Joy,' 'S.', 'P.']  This signify that we need to swap the first and last name.
            o_need_to_swap_flag = True
        return o_need_to_swap_flag

    def _rebuild_full_name_list(self, split_full_name):
        # Given a list of names that has been split into individual components
        # that may contains commas, rebuild the list to correct for the last name containing someone's title.
        # ['Bell', 'III,', 'J.F.'] becomes ['Bell III,', 'J.F.']
        # Function also handle case when there is no distinguishable way to parse the names such as ['PDS Geosciences Node']

        # By default take input as is to return.
        o_rebuilt_full_name = split_full_name 

        logger.debug(f"LEN_SPLIT_FULL_NAME {split_full_name,len(split_full_name)}")
        if len(split_full_name) == 3:
            # A comma in the 2nd element means that the last name spanned over two elements that need to be combined.
            o_rebuilt_full_name = []
            if ',' in split_full_name[1]: 
                # Combine the first element and second element together.
                o_rebuilt_full_name = [split_full_name[0].strip() + ' ' + split_full_name[1],
                                       split_full_name[2].strip()]
                logger.debug(f"REBUILT_FULL_NAME_LIST:THREE_COMMA {o_rebuilt_full_name,split_full_name,len(split_full_name)}")
            else:
                o_rebuilt_full_name = split_full_name 
        elif len(split_full_name) == 1:
            # Special cases for when there is no distinguishable way to parse the names such as ['PDS Geosciences Node']
            # where there is no separator of last and first name.
            # ['PDS Geosciences Node'] becomes ['Node', ['PDS Geosciences']
                names_token = split_full_name[0].split()
                logger.debug(f"GET_NAMES_SPECIAL:split_full_name,names_token {split_full_name,names_token}")
                if len(names_token) == 2:
                    o_rebuilt_full_name = [names_token[0], names_token[1]]  # ["John Doe"] becomes ["John","Doe"]
                elif len(names_token) >= 3:
                    # ['PDS Geosciences Node'] Becomes ['Node', ['PDS Geosciences']
                    o_rebuilt_full_name = [names_token[2], names_token[0] + ' ' + names_token[1]]
                #else:
                #    o_rebuilt_full_name = split_full_name
                logger.debug(f"GET_NAMES_SPECIAL:o_rebuilt_full_name,names_token,full_name {o_rebuilt_full_name,split_full_name,names_token}")

        logger.debug(f"REBUILT_FULL_NAME_LIST:FINALLY {o_rebuilt_full_name,split_full_name,len(split_full_name)}")
        return o_rebuilt_full_name, split_full_name

    def _rearrange_first_last_names(self, name_type, split_full_name, first_last_flag):
        # If the value of split_full_name is: ["Williams,", "David"] then
        # the last name is the one with the comma.
        # This function will return the names in this order ["David", "Williams"] with the comma removed.
        # There are serveral cases of the split_full_name:
        # Case 1: ["Williams", "David"]
        #         The array will need to be swapped.
        # Case 2: ["D.", "Williams"]
        #         This is the nominal case, take as is.
        # Case 3: ['Joy, S. P.', ' Mafi, J. N.', ' Slavney, S.', '']
        #         With last name, comma, then first and middle.
        # Case 4: [' Bell III, J.F.']

        # Rebuild the list of names to combine possible someone's title and check to see if the names need to be swapped.

        (rebuilt_full_name,original_name)   = self._rebuild_full_name_list(split_full_name)
        need_to_swap_flag                   = self._determine_need_to_swap_names_flag(rebuilt_full_name)

        o_reordered_full_name = rebuilt_full_name

        if '.' not in rebuilt_full_name[0]:
            if len(rebuilt_full_name) == 2:
                # The list ['Slavney,','S.' becomes  ['S.','Slavney']
                if first_last_flag == 0:
                    if need_to_swap_flag:
                        o_reordered_full_name = [rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[0].lstrip().rstrip().replace(',','')]
                    else:
                        o_reordered_full_name = [rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[0].lstrip().rstrip().replace(',','')]
                else:
                    o_reordered_full_name = [rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                             rebuilt_full_name[0].lstrip().rstrip().replace(',','')]
            elif len(rebuilt_full_name) >= 3:
                if first_last_flag == 0:
                    if need_to_swap_flag: # ['Mafi,', 'J.', 'N.']
                        o_reordered_full_name = [rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[2].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[0].lstrip().rstrip().replace(',','')]
                    else:
                        o_reordered_full_name = [rebuilt_full_name[0].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                                 rebuilt_full_name[2].lstrip().rstrip().replace(',','')]
                else:
                    # The list ['Joy,', 'S.', 'P.'] becomes 'S.', 'P.', 'Joy'] 
                    o_reordered_full_name = [rebuilt_full_name[1].lstrip().rstrip().replace(',',''),
                                             rebuilt_full_name[2].lstrip().rstrip().replace(',',''),
                                             rebuilt_full_name[0].lstrip().rstrip().replace(',','')]
        return o_reordered_full_name

    def _intelligent_parse_name(self, full_name,
                                first_last_name_order,
                                first_last_name_separators,
                                smart_first_name_detector=True):
        logger.debug(f"parse full_name {full_name}")

        full_name = full_name.lstrip().rstrip()

        person = None
        for sep in first_last_name_separators:
            fullname_splitted = full_name.split(sep)
            if len(fullname_splitted) >= 2:
                # use default first last name order
                [first_i, last_i] = first_last_name_order

                # unless we want to force initials to be first name
                if smart_first_name_detector:
                    if len(fullname_splitted[0]) == 1 or fullname_splitted[0][-1] == '.':
                      first_i, last_i = 0, -1
                    if len(fullname_splitted[-1]) == 1 or fullname_splitted[-1][-1] == '.':
                      first_i, last_i = -1, 0

                # re-add . if it has been removed as a separator
                first_name_suffix = '.' if sep == '.' else ''

                person = {'first_name': fullname_splitted[first_i].strip() + first_name_suffix,
                          'last_name': fullname_splitted[last_i].strip()}

                if len(fullname_splitted) >= 3:
                    person['middle_name'] = 1
                break

        if not person:
            person = {'full_name': full_name}

        logger.debug('parsed person {person}')

        return person


    # def _intelligent_parse_names(self, name_type, full_name, first_last_name_order, first_last_name_separator, io_persons):
    #     # Function parses the given full_name into individual fields 'first_name', 'last_name' and return the io_persons list.
    #     # Note that io_persons variable serves as both input and output.
    #     split_full_name = []
    #     separator_index = 0
    #     use_dot_split_flag = False
    #     use_comma_split_flag = False
    #     while len(split_full_name)<2 and separator_index<len(first_last_name_separator):
    #         if first_last_name_separator[separator_index] == '.':
    #             use_dot_split_flag = True
    #         if first_last_name_separator[separator_index] == ',':
    #             use_comma_split_flag = True
    #         split_full_name = full_name.strip().split(first_last_name_separator[separator_index])
    #         separator_index += 1
    #
    #     # If the value of split_full_name is: ["Williams,", "David"] then return ["David", "Williams"] with the comma removed.
    #     split_full_name = self._rearrange_first_last_names(name_type,split_full_name,first_last_name_order[0])
    #
    #     logger.debug(f"use_dot_split_flag {use_dot_split_flag}")
    #     logger.debug(f"split_full_name,len(split_full_name) {split_full_name,len(split_full_name)}")
    #     logger.debug(f"first_last_name_order {first_last_name_order}")
    #     logger.debug(f"use_dot_split_flag {use_dot_split_flag}")
    #
    #     if len(split_full_name) >= 2:
    #         # If the dot '.' was used to split the full_name, the dot need to be add back to the first name.
    #         corrected_first_name = split_full_name[0].strip()
    #         if use_dot_split_flag:
    #             corrected_first_name = corrected_first_name + "."
    #         if len(split_full_name) >= 3:
    #             io_persons.append({'first_name': corrected_first_name + " " + split_full_name[1].strip(),
    #                             'last_name'  : split_full_name[2].strip()})
    #         else:
    #             # Special case: If the last name is one character and the first name is more than one characters
    #             #               that means the first name and last name are swapped.
    #             #    Non-nominal case:['Maki', 'J']
    #             #    Nominal case    :['P.', 'Zamani']
    #             if len(split_full_name[1]) == 1 and len(split_full_name[0]) > 1:
    #                 one_person = {'first_name' : split_full_name[1] + '.',  # The first name needs a dot after as in 'J.'
    #                               'last_name'  : split_full_name[0]}        # The last name will be 'Maki'
    #             else:
    #                 one_person = {'first_name' : split_full_name[0],        # Nominal case: ['P.', 'Zamani']
    #                               'last_name'  : split_full_name[1]}
    #             io_persons.append(one_person)
    #     else:
    #         # If cannot parse first_name or last_name, create full_name instead.
    #         io_persons.append({'full_name': full_name.strip()})
    #
    #     return io_persons

    def get_names(self, name_list,
                  first_last_name_order=[0, -1],
                  first_last_name_separator=[',', '.']):
        logger.debug(f"name_list {name_list}")
        logger.debug(f"first_last_name_order {first_last_name_order}")
        persons = []
        for full_name in name_list:
            person = self._intelligent_parse_name(full_name, first_last_name_order, first_last_name_separator)
            persons.append(person)

        return persons

    def get_author_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[0, -1], first_last_name_separator=[',', '.'])

    def get_editor_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[-1, 0], first_last_name_separator=',')
