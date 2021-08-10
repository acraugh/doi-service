# coding: utf-8

from __future__ import absolute_import
from datetime import datetime  # noqa: F401

from pds_doi_service.api.models import Model
from pds_doi_service.api import util


class DoiRecord(Model):
    """
    NOTE: This class was auto generated by the swagger code generator program.
    """
    def __init__(self, doi=None, identifier=None, title=None,
                 node=None, submitter=None, status=None,
                 creation_date=None, update_date=None,
                 record=None, message=None):  # noqa: E501
        """DoiRecord - a model defined in Swagger

        :param doi: The doi of this DoiRecord.  # noqa: E501
        :type doi: str
        :param identifier: The PDS identifier of this DoiRecord.  # noqa: E501
        :type identifier: str
        :param title: The title of this DoiRecord.  # noqa: E501
        :type title: str
        :param node: The node of this DoiRecord.  # noqa: E501
        :type node: str
        :param submitter: The submitter of this DoiRecord.  # noqa: E501
        :type submitter: str
        :param status: The status of this DoiRecord.  # noqa: E501
        :type status: str
        :param creation_date: The creation_date of this DoiRecord.  # noqa: E501
        :type creation_date: datetime
        :param update_date: The update_date of this DoiRecord.  # noqa: E501
        :type update_date: datetime
        :param record: The record of this DoiRecord.  # noqa: E501
        :type record: str
        :param message: The message of this DoiRecord.  # noqa: E501
        :type message: str
        """
        self.swagger_types = {
            'doi': str,
            'identifier': str,
            'title': str,
            'node': str,
            'submitter': str,
            'status': str,
            'creation_date': datetime,
            'update_date': datetime,
            'record': str,
            'message': str
        }

        self.attribute_map = {
            'doi': 'doi',
            'identifier': 'identifier',
            'title': 'title',
            'node': 'node',
            'submitter': 'submitter',
            'status': 'status',
            'creation_date': 'creation_date',
            'update_date': 'update_date',
            'record': 'record',
            'message': 'message'
        }
        self._doi = doi
        self._identifier = identifier
        self._title = title
        self._node = node
        self._submitter = submitter
        self._status = status
        self._creation_date = creation_date
        self._update_date = update_date
        self._record = record
        self._message = message

    @classmethod
    def from_dict(cls, dikt) -> 'DoiRecord':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The doi_record of this DoiRecord.  # noqa: E501
        :rtype: DoiRecord
        """
        return util.deserialize_model(dikt, cls)

    @property
    def doi(self) -> str:
        """Gets the doi of this DoiRecord.


        :return: The doi of this DoiRecord.
        :rtype: str
        """
        return self._doi

    @doi.setter
    def doi(self, doi: str):
        """Sets the doi of this DoiRecord.


        :param doi: The doi of this DoiRecord.
        :type doi: str
        """

        self._doi = doi

    @property
    def identifier(self) -> str:
        """Gets the PDS identifier of this DoiRecord.


        :return: The identifier of this DoiRecord.
        :rtype: str
        """
        return self._identifier

    @identifier.setter
    def identifier(self, identifier: str):
        """Sets the PDS identifier of this DoiRecord.


        :param identifier: The identifier of this DoiRecord.
        :type identifier: str
        """

        self._identifier = identifier

    @property
    def title(self) -> str:
        """Gets the title of this DoiRecord.


        :return: The title of this DoiRecord.
        :rtype: str
        """
        return self._title

    @title.setter
    def title(self, title: str):
        """Sets the title of this DoiRecord.


        :param title: The title of this DoiRecord.
        :type title: str
        """

        self._title = title

    @property
    def node(self) -> str:
        """Gets the node of this DoiRecord.


        :return: The node of this DoiRecord.
        :rtype: str
        """
        return self._node

    @node.setter
    def node(self, node: str):
        """Sets the node of this DoiRecord.


        :param node: The node of this DoiRecord.
        :type node: str
        """

        self._node = node

    @property
    def submitter(self) -> str:
        """Gets the submitter of this DoiRecord.


        :return: The submitter of this DoiRecord.
        :rtype: str
        """
        return self._submitter

    @submitter.setter
    def submitter(self, submitter: str):
        """Sets the submitter of this DoiRecord.


        :param submitter: The submitter of this DoiRecord.
        :type submitter: str
        """

        self._submitter = submitter

    @property
    def status(self) -> str:
        """Gets the status of this DoiRecord.


        :return: The status of this DoiRecord.
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status: str):
        """Sets the status of this DoiRecord.


        :param status: The status of this DoiRecord.
        :type status: str
        """

        self._status = status

    @property
    def creation_date(self) -> datetime:
        """Gets the creation_date of this DoiRecord.


        :return: The creation_date of this DoiRecord.
        :rtype: datetime
        """
        return self._creation_date

    @creation_date.setter
    def creation_date(self, creation_date: datetime):
        """Sets the creation_date of this DoiRecord.


        :param creation_date: The creation_date of this DoiRecord.
        :type creation_date: datetime
        """

        self._creation_date = creation_date

    @property
    def update_date(self) -> datetime:
        """Gets the update_date of this DoiRecord.


        :return: The update_date of this DoiRecord.
        :rtype: datetime
        """
        return self._update_date

    @update_date.setter
    def update_date(self, update_date: datetime):
        """Sets the update_date of this DoiRecord.


        :param update_date: The update_date of this DoiRecord.
        :type update_date: datetime
        """

        self._update_date = update_date

    @property
    def record(self) -> str:
        """Gets the record of this DoiRecord.


        :return: The record of this DoiRecord.
        :rtype: str
        """
        return self._record

    @record.setter
    def record(self, record: str):
        """Sets the record of this DoiRecord.


        :param record: The record of this DoiRecord.
        :type record: str
        """

        self._record = record

    @property
    def message(self) -> str:
        """Gets the message of this DoiRecord.


        :return: The message of this DoiRecord.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message: str):
        """Sets the message of this DoiRecord.


        :param message: The message of this DoiRecord.
        :type message: str
        """

        self._message = message
