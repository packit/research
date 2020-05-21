# Research public cloudz as a place to run packit-service  
  
Puprpose of this document is to get information about possible clouds for packit-service hosting, costs and efforts. Based on the collected data in this card, we should be able to choose the right place for packit-service. 
  
**AC:** 
- make sure the requirements doc is up to date  
- research what would be the maintenance cost to have openshift 4 on azure:  
  -  cost  
  - our capacity  
- check what storage types there are in azure and compare performance (SSD vs HDD)  
- consider terraform, ansible and the official openshift installer  
- other people in the cyborg group already did some research, get in touch  
- Michael Hoffman is researching AWS, get in touch with him  
  
**To consider**
managed vs. self manged:
* managed: 
	* no installation, maintenance and oc administration knowledge required
	* expensive
* self managed:
	* installation should be "easy"
	* maintenance will require moderate effort (also depends on stability of underlying layers)
	* will we require test instance 
  
## Alternatives:
  
### Azure
[cost calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
* OpenShift4 (managed):
	* cost (3 year commitment)
		Upfront cost: ~$43,670.18
		Monthly cost: ~$2.90
		(have to figure out how heavy load will affect monthly/overall costs)

* OpenShift4 (self managed) :
	* (have to put together minimal requirements)
  
### AWS + kubernetes :

### PSI:
Is running on OpenStack and is unstable - will cause lot of issue

* **PSI + OpenShift3 (4?) (PHX manged)** 
  * should be available in 3-4 months

* **PSI + OpenShift4 (PHX self manged)**
  * full time job - we expect lot of issues on multiple layers (hw, openstack, opneshit)
  * first hw should be available 24. 5. 2020 and next bigger bunch 3 weeks later, PSI expects high demand for public clouds, but they should be able to onboard, still it will be our choice we should get in touch with them ASAP
  
* **PSI + Openshift (managed)**
  * no public access currently, there is ongoing dicusssion about publict access, but is in early stage and can took 6-12 months (maybe longer).  



## TODO
* get more details about maintenance tasks
* links
* try to get as close cost estimations as possible
* research usefull services (alternative to redis, postgres, ?)
