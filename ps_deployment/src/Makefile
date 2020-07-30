build_github_base:
	docker build . --file Dockerfile_github_base -t ps_normal_github_base --no-cache
build_github_final:
	docker build . --file Dockerfile_github_final -t ps_normal_github_final --no-cache
	
	
build_rpm_base:
	docker build . --file Dockerfile_rpm_base -t ps_normal_rpm_base --no-cache
build_rpm_final:
	docker build . --file Dockerfile_rpm_final -t ps_normal_rpm_final --no-cache
	

build_s2i_base:
	docker build . --file Dockerfile_s2i_github_base -t ps_s2i_github_base --no-cache
build_s2i_final:
	s2i build . ps_s2i_github_base ps_s2i_github_final --loglevel=1
