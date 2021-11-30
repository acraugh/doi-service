#!/usr/bin/env python
import os
import shutil
import unittest

from datetime import datetime
from pkg_resources import resource_filename

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi, ProductType, DoiStatus
from pds_doi_service.core.outputs.datacite.datacite_record import DOIDataCiteRecord
from pds_doi_service.core.outputs.datacite.datacite_web_parser import DOIDataCiteWebParser
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.transaction import Transaction
from pds_doi_service.core.outputs.transaction_builder import TransactionBuilder
from pds_doi_service.core.outputs.transaction_on_disk import TransactionOnDisk


class TransactionTestCase(unittest.TestCase):
    db_name = "doi_temp.db"

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = resource_filename(__name__, "")

        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def test_transaction_logging(self):
        """Test the Transaction.log() method"""
        # Create a fresh transaction database
        doi_database = DOIDataBase(self.db_name)

        # Create a dummy Doi object an associated output label to log
        test_doi = Doi(
            title="Fake DOI",
            publication_date=datetime.now(),
            product_type=ProductType.Dataset,
            product_type_specific="PDS4 Dataset",
            pds_identifier="urn:nasa:pds:fake_doi_entry::1.0",
            doi="10.17189/abc123",
            status=DoiStatus.Draft,
            date_record_added=datetime.now(),
            date_record_updated=datetime.now()
        )

        output_content = DOIDataCiteRecord().create_doi_record(test_doi)
        output_content_type = CONTENT_TYPE_JSON
        node_id = "eng"
        submitter_email = "pds-operator@jpl.nasa.gov"

        # Create a Transaction object and log it
        transaction = Transaction(
            output_content, output_content_type, node_id, submitter_email, test_doi, doi_database
        )

        transaction_key = None

        try:
            transaction.log()

            # Logging should result in an entry written to the database, check for it
            # now
            columns, rows = doi_database.select_latest_rows(
                query_criterias={"doi": ["10.17189/abc123"]}
            )

            self.assertEqual(len(rows), 1)

            db_fields = dict(zip(columns, rows[0]))

            self.assertEqual(db_fields["title"], "Fake DOI")
            self.assertEqual(db_fields["identifier"], "urn:nasa:pds:fake_doi_entry::1.0")

            # An entry in the local transaction history should have been written as well
            transaction_key = db_fields["transaction_key"]
            self.assertIsNotNone(transaction_key)
            self.assertTrue(os.path.isdir(transaction_key))
        finally:
            # Clean up the fake transaction, if it was created
            if transaction_key and os.path.exists(transaction_key):
                shutil.rmtree(transaction_key)


class TransactionBuilderTestCase(unittest.TestCase):
    db_name = "doi_temp.db"

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = resource_filename(__name__, "")

        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def test_prepare_transaction(self):
        """Test the TransactionBuilder.prepare_transaction() method"""
        # Create a fresh transaction database and populate it with an existing entry
        doi_database = DOIDataBase(self.db_name)

        identifier = "urn:nasa:pds:existing_doi::1.0"
        transaction_key = "img/2020-06-15T18:42:45.653317"
        doi = "10.17189/abc123"
        date_added = datetime.now()
        date_updated = datetime.now()
        status = DoiStatus.Draft
        title = "Existing DOI"
        product_type = ProductType.Collection
        product_type_specific = "PDS4 Collection"
        submitter = "img-submitter@jpl.nasa.gov"
        discipline_node = "img"

        # Insert a row in the 'doi' table
        doi_database.write_doi_info_to_database(
            doi,
            transaction_key,
            identifier,
            date_added,
            date_updated,
            status,
            title,
            product_type,
            product_type_specific,
            submitter,
            discipline_node,
        )

        # Create the transaction builder and have it point to the same database
        transaction_builder = TransactionBuilder(db_name=self.db_name)

        # Create a Doi object to be handled by the transaction builder
        test_doi = Doi(
            title=title,
            publication_date=datetime.now(),
            product_type=ProductType.Dataset,
            product_type_specific="PDS4 Dataset",
            pds_identifier="",
            doi=doi,
            status=DoiStatus.Draft,
            date_record_updated=datetime.now()
        )

        # Create the transaction from the Doi
        transaction = transaction_builder.prepare_transaction(
            node_id=discipline_node, submitter_email=submitter, doi=test_doi,
            output_content_type=CONTENT_TYPE_JSON
        )

        self.assertIsInstance(transaction, Transaction)

        # Get the output label created by the transaction builder and make sure
        # it lines up with our original DOI
        output_content = transaction.output_content

        output_dois, _ = DOIDataCiteWebParser().parse_dois_from_label(output_content)

        self.assertEqual(len(output_dois), 1)

        output_doi = output_dois[0]

        # These two fields should be carried over from the existing database entry,
        # since they were not provided with the Doi object we prepared the transaction
        # for
        self.assertEqual(output_doi.pds_identifier, identifier)
        self.assertEqual(output_doi.date_record_added.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                         date_added.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))


class TransactionOnDiskTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = resource_filename(__name__, "")
        cls.data_dir = os.path.join(cls.test_dir, "data")

    def test_transaction_write_to_disk(self):
        """Test the TransactionOnDisk.write() method"""

        transaction_on_disk = TransactionOnDisk()

        node_id = "eng"
        transaction_time = datetime.now()

        # Test a transaction commit to disk
        input_label = os.path.join(self.data_dir, "pds4_bundle.xml")
        output_label = os.path.join(self.data_dir, "datacite_record_draft.json")

        with open(output_label, 'r') as infile:
            output_content = infile.read()

        transaction_key = None

        try:
            transaction_key = transaction_on_disk.write(
                node_id, transaction_time, input_ref=input_label,
                output_content=output_content, output_content_type=CONTENT_TYPE_JSON
            )

            # Make sure the transaction directory was created as expected
            self.assertTrue(os.path.exists(transaction_key))
            self.assertTrue(os.path.isdir(transaction_key))

            # Make sure the directory was created with the correct permissions
            expected_perms = 0o0755
            self.assertEqual(os.stat(transaction_key).st_mode & expected_perms, expected_perms)

            # Make sure the input and output files were copied as expected
            expected_input_file = os.path.join(transaction_key, "input.xml")
            expected_output_file = os.path.join(transaction_key, "output.json")
            expected_perms = 0o0664

            for test_file, expected_file in zip((input_label, output_label), (expected_input_file, expected_output_file)):
                # Check existence
                self.assertTrue(os.path.exists(expected_file))
                self.assertTrue(os.path.isfile(expected_file))

                # Check contents
                with open(test_file, 'r') as infile:
                    test_file_contents = infile.read()

                with open(expected_file, 'r') as infile:
                    expected_file_contents = infile.read()

                self.assertEqual(test_file_contents, expected_file_contents)

                # Check permissions
                self.assertEqual(os.stat(expected_file).st_mode & expected_perms, expected_perms)
        finally:
            # Cleanup the transaction dir if it was created
            if transaction_key and os.path.exists(transaction_key):
                shutil.rmtree(transaction_key)


if __name__ == "__main__":
    unittest.main()
