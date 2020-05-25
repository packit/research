# Research public cloudz as a place to run packit-service  
  
Purpose of this document is to get information about possible clouds for packit-service hosting, costs and efforts. Based on the collected data in this card, we should be able to choose the right place for packit-service. 
  
**AC:** 
- make sure the [requirements doc](https://docs.google.com/document/d/1McQCjokq9tgywZ8-ydMX_U7ymYxne5O_jyi4yRlnTqM/edit) is up to date  
- research what would be the maintenance cost to have openshift 4 on azure:  
  - cost  
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
	
* self managed (some of below and be counted as "hidden" costs):
	* installation should be "easy"
	* maintenance will require moderate effort (also depends on stability of underlying layers)
		platform related:
		* monitoring
		* backups
		* recovery plan - can be helpful also in case we will break something and it will take significant time to investigate and fix
		openshift related:
		(#TODO - get idea about daily mainatainance tasks and common issues)
	* will we require test instance to prepare some acttions?
	
SSD vs. HDD:
* in our environment it should be enough to have HDD, with option to upgrade to SSD in case of need. Upgrade will consist of data migration to new volume, cloud platform should be well prepared for such scenario. (detatiled data migration research out of scope)

* high probably, we will have to pay for RedHat linux subscription, is it possible to avoid that?
  
## Alternatives:
  
### Azure
[cost calculator](https://azure.microsoft.com/en-us/pricing/calculator/)\
B-tier vs. D-tier VM series - B is cheaper but less powerfull, D is "enterprise level"\
[disk performance comparisson](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/disks-types)\

* OpenShift4 (managed):
	* [cost (3 year commitment)](https://azure.com/e/59ac45f6d41b4e3eba11846817fcd11e)
		* Upfront cost: ~$43,670.18
		* Monthly cost: ~$2.90

* OpenShift4 (self managed) :
	*  [pay-as-you-go - installer default requirements](https://azure.com/e/2168c57a7dd144e0ab7d5e4f40c794ba)
		* Estimated monthly cost: $1,841.09
	*  [3 year commitment - installer default requirements](https://azure.com/e/19bb77f22082408fa73bfbeb85f1a1f2)
		* Estimated monthly cost: $1,103.52
	*  [pay-as-you-go - minimal requirements](https://azure.com/e/0172ab3e35bf4fbeaf68bc59d3542773)
		* Estimated monthly cost: $1,004.51
	*  [3 year commitment - minimal requirements](https://azure.com/e/8baba032d43d4433977298c04974d33c)
		* Estimated monthly cost: $611.30

  
### AWS fedora + kubernetes:
* for free
* requires hands-on to be able to determine if our ansible based deployment is compatible with kubernetes and if is worth to migrate 
	
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
* AWS research
* links
* try to get as close cost estimations as possible
* research usefull services (alternative to redis, postgres, ?)
* mutiple avaibality zones, how it will affect costs
