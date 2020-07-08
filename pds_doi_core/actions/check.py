#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import json
import os
import pystache

from copy import deepcopy
from datetime import date
from types import SimpleNamespace

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.actions.list import DOICoreActionList
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.emailer import Emailer
from pds_doi_core.references.contributors import DOIContributorUtil

class DOICoreActionCheck(DOICoreAction):
    _name = 'check'
    description = ' % pds-doi-cmd check \n' 

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        self._doi_web_client = DOIOstiWebClient()
        self._emailer = Emailer()

        self._set_criterias()            # Set any search query criteria if there are any.

        self._list_obj = DOICoreActionList(db_name=db_name)

    def _set_criterias(self):
        self._query_criterias = {}
        # Add the 'Pending' status to get only rows with 'Pending' status only.
        self._query_criterias['status'] = 'Pending'

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)

    def _process_one_query_result(self, pending_state_list, check_result_dict, output_content='', web_response=None):
        """
        Function process the result from the one 'check' query to OSTI server.  If the status has changed from initial status,
        update the old record in the database and write a new record to the database and return DOI just updated.
        :param pending_state_list:
        :param check_result_dict:
        :param output_content:
        :param web_response:
        :return: o_doi_updated:
        """

        o_doi_updated_dict = {} 
        logger.debug(f"pending_state_list {pending_state_list}")
        logger.debug(f"check_result_dict {check_result_dict}")
        logger.debug(f"output_content {output_content}")
        logger.debug(f"web_response {web_response}")

        pending_state_dois_list = [element['doi']    for element in pending_state_list]

        # Do a sanity check if the same DOI can be found in pending_state_list.
        
        if check_result_dict['doi'] in pending_state_dois_list:
            index_found = pending_state_dois_list.index(check_result_dict['doi'])
            logger.debug(f"DOI initial_status status {check_result_dict['doi'],pending_state_list[index_found]['status'],check_result_dict['status']}")

            # If the status has changed from what was in the database, write a record to the database otherwise do nothing.
            # An example change from 'Pending' to 'Assigned'
            if pending_state_list[index_found]['status'].lower() != check_result_dict['status'].lower():
                logger.debug(f"STATUS_YES_CHANGED:{check_result_dict['doi'],pending_state_list[index_found]['status'],check_result_dict['status']}")
                # Write a small file to disk and pass this filename to prepare_transaction() function as input parameter.
                now_is = datetime.datetime.now().isoformat()
                temporary_file_name = "OSTI_status_check_on_" + now_is + ".xml"
                temporary_file_ptr = open(temporary_file_name,"w+") 
                temporary_file_ptr.write("OSTI_status_check_at " + now_is + "\n")
                temporary_file_ptr.close()

                # Update the 'status' field and massage the dict pending_state_list[index_found] into a structure that prepare_transaction() would recognize.
                pending_state_list[index_found]['status'] = check_result_dict['status']
                pending_state_list[index_found]['related_identifier'] = pending_state_list[index_found]['lid'] + '::' + pending_state_list[index_found]['vid']
                pending_state_list[index_found]['product_type'] = pending_state_list[index_found]['type']
                pending_state_list[index_found]['product_type_specific'] = pending_state_list[index_found]['subtype']

                # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
                transaction_obj = self.m_transaction_builder.prepare_transaction(temporary_file_name,
                                                                                 pending_state_list[index_found]['node_id'],
                                                                                 pending_state_list[index_found]['submitter'],
                                                                                 [pending_state_list[index_found]],
                                                                                 output_content=output_content,
                                                                                 web_response=web_response)

                # Write a transaction for the 'check' action.
                transaction_obj.log()
                if os.path.isfile(temporary_file_name):
                    os.remove(temporary_file_name) # Remove temporary file.

                # Save the DOI updated.
                o_doi_updated_dict = {'doi':check_result_dict['doi'],'initial_status':'Pending','status':check_result_dict['status']}

            else:
                logger.debug(f"STATUS_NO_CHANGED:{check_result_dict['doi'],pending_state_list[index_found]['status'],check_result_dict['status']}")
                pass

        else:
            pass

        return o_doi_updated_dict

    def _get_distinct_submitters(self, i_check_result):
        """Function get a list of dictinct submitter from a list of metadata i_check_result."""
        o_distinct_submitters = []

        for ii in range(0,len(i_check_result)):
            if i_check_result[ii]['submitter'].lower() not in o_distinct_submitters:
               o_distinct_submitters.append(i_check_result[ii]['submitter'].lower()) 
        # end for ii in range(0,len(i_check_result)):

        return o_distinct_submitters

    def _get_status_per_submitter(self, i_check_result, i_submitter):
        """Function return a list of dictionaries that contains the field same as given submitter."""
        o_dicts_per_submitter = []

        for ii in range(0,len(i_check_result)):
            if i_check_result[ii]['submitter'].lower() == i_submitter:
               o_dicts_per_submitter.append(i_check_result[ii])
        # end for ii in range(0,len(i_check_result)):

        return o_dicts_per_submitter 


    def _get_status_per_submitter_per_node(self, i_check_result, i_submitter):
        """Function return a dictionary of lists for different nodes for a particular submitter."""
        o_dicts_per_submitter_per_node = {} 

        for ii in range(0,len(i_check_result)):
            if i_check_result[ii]['submitter'].lower() == i_submitter:
               node_key = i_check_result[ii]['node_id'].lower()
               if node_key not in o_dicts_per_submitter_per_node:
                   o_dicts_per_submitter_per_node[node_key] = [] # Start with an empty list.
               o_dicts_per_submitter_per_node[node_key].append(i_check_result[ii])
                  
        # end for ii in range(0,len(i_check_result)):

        return o_dicts_per_submitter_per_node

    def _prepare_attachment(self, i_dicts_per_submitter):
        """Prepare an attachment by converting i_dicts_per_submitter to a JSON text and return the o_attachment_part as MIMEMultipart object."""

        # Only do the import if sending an attachment file along with the email.
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        # Convert a list of dict to JSON text to make it human readable.
        attachment_text = json.dumps(i_dicts_per_submitter,indent=4)  # Make human read-able output with indentation of each key.

        now_is = datetime.datetime.now().isoformat()
        o_attachment_filename = 'doi_status_attachment_on_' + now_is + '.txt'  # Add current time to make file unique

        # Write the attachment_text to disk so the file can be sent as an attachment.
        file_ptr = open(o_attachment_filename,"w+")
        file_ptr.write(attachment_text)
        file_ptr.close()

        o_attachment_part = MIMEMultipart()
        part = MIMEBase('application', 'text')
        part.add_header('Content-Disposition', "attachment; filename= %s" % o_attachment_filename)
        part.set_payload(attachment_text)
        o_attachment_part.attach(part)

        # Must return the attachment filename so it can be deleted after the email has been successfully sent.
        return (o_attachment_filename,o_attachment_part)

    def _prepare_email_entire_message(self, i_dicts_per_submitter):
        renderer = pystache.Renderer()
        today = date.today()

        # There is an 'Id' column in the email content so that field needs to be built.
        # The field 'record_index' is to allow Pystache to print the record number on the left most column.
        record_index = 0
        for doi_record in i_dicts_per_submitter:
            doi_record['id'] = doi_record['doi'].split('/')[1]   # Split '10.17189/21940' to get to 21940
            doi_record['record_index'] = record_index + 1
            record_index += 1

        # Build the email first part containing: Date: 07/01/2020\n 3 records.
        header_dict = {'my_date':today.strftime("%m/%d/%Y"),'my_records_count':len(i_dicts_per_submitter)}
        email_part_1 = renderer.render_path('config/emailer_template_part_1-mustache.json', header_dict)

        # Build the email second part containing the table of DOIs with status changed: "1  21940  Laboratory Shocked Feldspars Bundle  10.17189/21940  Pending  Reserved"
        email_part_2 = renderer.render_path('config/emailer_template_part_2-mustache.json', {'dois': i_dicts_per_submitter})

        o_email_entire_message = email_part_1 + "\n" + email_part_2
        logger.debug(f"o_email_entire_message {o_email_entire_message}")

        return o_email_entire_message

    def _send_email(self,to_send_attachment_flag,email_sender,final_receivers,subject_field,email_entire_message,o_dicts_per_submitter_per_node,node_key): 

        if not to_send_attachment_flag:
            self._emailer.sendmail(email_sender, final_receivers, subject_field, email_entire_message) # This send a brief email message.
        else:
            # Try an alternative way to send the email so the attachment will be view as an attachment in the email reader.
            # Only do the import if sending an attachment file along with the email.
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"]     = email_sender 
            msg["Subject"]  = subject_field
            msg["To"]       = final_receivers

            msg.set_content(email_entire_message)

            (attachment_filename,attachment_part) = self._prepare_attachment(o_dicts_per_submitter_per_node[node_key])
            msg.add_attachment(attachment_part)  # The attachment is now 'attached' in the msg object.

            # Send the email with attachment file.
            self._emailer.send_message(msg)

            # Delete the temporary attached file.
            if os.path.isfile(attachment_filename):
                os.remove(attachment_filename) # Remove temporary file.

        return 1


    def _process_dois_updated_records(self, i_check_result, to_send_mail_flag=False, to_send_attachment_flag=False):
        """From all records in i_check_result, group a list of records per submitter and send an email
           of the status of metadata of DOIs with status changed to receivers."""

        logger.debug(f"to_send_mail_flag {to_send_mail_flag}")

        # Get configurations related to sending email.
        email_sender           = self._config.get('OTHER', 'emailer_sender')
        email_receivers_field  = self._config.get('OTHER', 'emailer_receivers')
        email_receivers_tokens = email_receivers_field.split(',')  # The receivers can be a list of addresses with comma separated.
        email_receivers = []

        # Get a distint list of email addresses from email_receivers_field in case they have duplicates.
        for email_receiver_token in email_receivers_tokens:
            if email_receiver_token.lstrip().rstrip().lower() not in email_receivers:
                email_receivers.append(email_receiver_token.lstrip().rstrip().lower())

        # Get distinct submitter from i_check_result
        distinct_submitters = self._get_distinct_submitters(i_check_result)

        # From email_receivers and distinct_submitters, create a new unique list of email recipient.
        distinct_receivers = []
        distinct_receivers.extend(email_receivers)

        for distinct_submitter in distinct_submitters:
            if distinct_submitter not in distinct_receivers:
                distinct_receivers.append(distinct_submitter)

        now_is = datetime.datetime.now().isoformat()
        subject_field = "DOI Submission Status Report On " + now_is

        # For each distinct submitter found in all dictionary i_check_result, send email to that submitter
        # of all records that have changed from 'Pending' to something else.
        for distinct_submitter in distinct_submitters:
            # Build a list of unique recipients for the emailer.
            final_receivers = deepcopy(distinct_receivers) 
            if distinct_submitter not in final_receivers:
                final_receivers.append(distinct_submitter)

            # Loop through i_check_result and get all records submitted by that submitter.

            o_dicts_per_submitter = self._get_status_per_submitter(i_check_result,distinct_submitter)

            # It may be that for each submitter, there may be more than one node.
            o_dicts_per_submitter_per_node = self._get_status_per_submitter_per_node(o_dicts_per_submitter,distinct_submitter) 

            for node_key in list(o_dicts_per_submitter_per_node.keys()):
                subject_field = "DOI Submission Status Report For Node '" + node_key + "'  On " + now_is

                # Convert a list of dict to JSON text to make it human readable.
                dois_per_submitter = [element['doi'] for element in o_dicts_per_submitter_per_node[node_key]]
                logger.debug(f"SUBMITTER_AND_NUM_RECORDS_PER_SUBMITTER {distinct_submitter,node_key,len(o_dicts_per_submitter_per_node[node_key]),dois_per_submitter}")

                # Prepare the email message using all the dictionaries.
                email_entire_message = self._prepare_email_entire_message(o_dicts_per_submitter_per_node[node_key])

                # Finally send the email with all statuses per submitter per node.
                if to_send_mail_flag:
                    self._send_email(to_send_attachment_flag,email_sender,final_receivers,subject_field,email_entire_message,o_dicts_per_submitter_per_node,node_key)

        return 1

    def run(self,
            query_criterias=[], to_send_mail_flag=True, to_send_attachment_flag=True):
        """
        Function query the local database for latest records for pending state and check OSTI server all the records with criteria specified in query_criterias return the object either in JSON or XML.
        Once the query is returned every record will be checked for initial status and status returned from OSTI.
        If the status has changed from initial status, write a new record to the database.
        All parameters are optional and may be useful for tests.
        :param output_format:
        :param query_criterias:
        :param to_send_mail_flag:
        :param to_send_attachment_flag:
        :return: o_check_result:
        """

        logger.debug(f"to_send_mail_flag {to_send_mail_flag}")
        o_check_result = []

        # Get the list of latest rows in database with status = 'Pending'.
        if len(query_criterias) > 0: 
            # Use query_criterias if provided from user.
            o_doi_list = self._list_obj.run(query_criterias=query_criterias)
        else:
            # Get the list of latest rows in database with status = 'Pending' using the private self._query_criterias.
            o_doi_list = self._list_obj.run(query_criterias=self._query_criterias)

        # Convert from JSON into a list.
        pending_state_list = []
        if len(o_doi_list) > 0:
            pending_state_list = json.loads(o_doi_list)

        # Variable pending_state_list is now list of records with 'Pending status.

        logger.debug(f"pending_state_list {pending_state_list,len(pending_state_list)}")

        # For every doi_value in doi_list, make a query to the server for the status and update the state in the database.

        i_url = self._config.get('OSTI', 'url')

        for pending_record in pending_state_list:
            logger.debug(f"pending_record {pending_record}")
            doi_value = pending_record['doi']
            query_dict = {'doi':doi_value}
            o_response_dict = self._doi_web_client.webclient_query_doi(i_url,
                                                                       query_dict,
                                                                       i_username=self._config.get('OSTI', 'user'),
                                                                       i_password=self._config.get('OSTI', 'password'))

            # Depending on what the OSTI server has, the value of o_response_dict can be an empty JSON string '[]'.

            result_as_list = json.loads(o_response_dict)  # Convert the JSON string to a Python list.

            # Variable result_as_list is now a list and can be empty if the value of o_response_dict is a JSON string of '[]'.
        
            logger.debug(f"result_as_list {result_as_list}")
            logger.debug(f"len(result_as_list) {len(result_as_list)}")
            
            # If the DOI was found on the OSTI server, process it.  We are expecting at least 1 record if found.
            if len(result_as_list) > 0:
                doi_updated_dict = self._process_one_query_result(pending_state_list,result_as_list[0],output_content='')
                # Keep track of a list of DOIs updated in the database by adding two new fields to pending_record dict.
                if 'initial_status' in doi_updated_dict and 'status' in doi_updated_dict:
                    pending_record['initial_status'] = doi_updated_dict['initial_status'] 
                    pending_record['status']         = doi_updated_dict['status']    # This is now the new state of the previously 'Pending'
                    o_check_result.append(pending_record)
        # end for pending_record in pending_state_list:

        # If there are list of DOIs with status changed, process them.
        if len(o_check_result) > 0:
            #self._process_dois_updated_records(o_check_result,to_send_mail_flag)
            self._process_dois_updated_records(o_check_result,to_send_mail_flag,to_send_attachment_flag)
            #self._process_dois_updated_records(o_check_result,to_send_mail_flag,to_send_attachment_flag=True):

        # Return a list of DOIs updated.  List can be empty meaning no records have changed from 'Pending' to something else.
        return o_check_result

# end class DOICoreActionCheck(DOICoreAction):