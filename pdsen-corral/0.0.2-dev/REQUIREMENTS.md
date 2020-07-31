
Requirements Summary
====================

# DOI management

## The software shall be capable of accepting a request to create a draft DOI. ([#5](https://github.com/NASA-PDS/pds-doi-service/issues/5)) 


This requirement is not impacted by the current version
## The software shall be capable of accepting a request to reserve a DOI. ([#6](https://github.com/NASA-PDS/pds-doi-service/issues/6)) :boom:


The enhancements which impact this requirements are:
- DOI Batch Processing capability ([#25](https://github.com/NASA-PDS/pds-doi-service/issues/25))
- Design REST API and JSON response ([#19](https://github.com/NASA-PDS/pds-doi-service/issues/19))
- Reserve a DOI capability ([#21](https://github.com/NASA-PDS/pds-doi-service/issues/21))

## The software shall be capable of accepting a request to release a DOI. ([#7](https://github.com/NASA-PDS/pds-doi-service/issues/7)) :boom:


The enhancements which impact this requirements are:
- Implement the command line and parser to release a doi ([#46](https://github.com/NASA-PDS/pds-doi-service/issues/46))
- DOI Batch Processing capability ([#25](https://github.com/NASA-PDS/pds-doi-service/issues/25))
- Design REST API and JSON response ([#19](https://github.com/NASA-PDS/pds-doi-service/issues/19))
- Release DOI capability ([#22](https://github.com/NASA-PDS/pds-doi-service/issues/22))

## The software shall be capable of accepting a request to deactivate a DOI. ([#8](https://github.com/NASA-PDS/pds-doi-service/issues/8)) :boom:


The enhancements which impact this requirements are:
- DOI Batch Processing capability ([#25](https://github.com/NASA-PDS/pds-doi-service/issues/25))
- Design REST API and JSON response ([#19](https://github.com/NASA-PDS/pds-doi-service/issues/19))

## The software shall be capable of accepting a request to update DOI metadata. ([#9](https://github.com/NASA-PDS/pds-doi-service/issues/9)) :boom:


The enhancements which impact this requirements are:
- Update Released DOI capability ([#24](https://github.com/NASA-PDS/pds-doi-service/issues/24))
- DOI Batch Processing capability ([#25](https://github.com/NASA-PDS/pds-doi-service/issues/25))
- Design REST API and JSON response ([#19](https://github.com/NASA-PDS/pds-doi-service/issues/19))

## The software shall be capable of batch processing >1 DOI requests.	 ([#10](https://github.com/NASA-PDS/pds-doi-service/issues/10)) :boom:


The enhancements which impact this requirements are:
- DOI Batch Processing capability ([#25](https://github.com/NASA-PDS/pds-doi-service/issues/25))
- Design REST API and JSON response ([#19](https://github.com/NASA-PDS/pds-doi-service/issues/19))

# DOI metadata

## The software shall be capable of autonomously generating the minimum set of DOI metadata from PDS4 Collection, Bundle, Document products. ([#11](https://github.com/NASA-PDS/pds-doi-service/issues/11)) 


This requirement is not impacted by the current version
## The software shall validate a minimum set of metadata is provided when reserving, releasing, or updating a DOI. This minimum set of metadata will be defined by the PDS DOI Working Group. ([#12](https://github.com/NASA-PDS/pds-doi-service/issues/12)) 


This requirement is not impacted by the current version
## The software shall validate the DOI metadata when reserving, releasing, or updating a DOI. ([#13](https://github.com/NASA-PDS/pds-doi-service/issues/13)) 


This requirement is not impacted by the current version
#  DOI interface support

## The software shall maintain a database of PDS DOIs and their current state. ([#14](https://github.com/NASA-PDS/pds-doi-service/issues/14)) 


This requirement is not impacted by the current version
## The software shall maintain the ability to manage DOIs through OSTI ([#15](https://github.com/NASA-PDS/pds-doi-service/issues/15)) 


This requirement is not impacted by the current version
## The software shall maintain the ability to manage DOIs through DataCite. ([#16](https://github.com/NASA-PDS/pds-doi-service/issues/16)) 


This requirement is not impacted by the current version
# DOI-management

## The software shall provide a Status capability that will allow a user to query for the current status of a DOI ([#30](https://github.com/NASA-PDS/pds-doi-service/issues/30)) :boom:


The enhancements which impact this requirements are:
- Develop DOI Status / Query component ([#27](https://github.com/NASA-PDS/pds-doi-service/issues/27))

## The software shall provide the capability of producing a DOI Status Report based upon a user-specified query ([#35](https://github.com/NASA-PDS/pds-doi-service/issues/35)) 


This requirement is not impacted by the current version