.PHONY: usage convert clean

PACKAGE ?= rpm
BRANCH ?= c8s
DIR ?= git.centos.org

usage:
	@echo "Run 'make convert' to run the convert or 'make clean' to clean up things."
	@echo ""
	@echo "Set 'PACKAGE' to pick a package from git.centos.org/rpms. Defaults to '$(PACKAGE)'."
	@echo "Set 'BRANCH' to select the branch to convert. Defaults to '$(BRANCH)'."
	@echo "Set 'DIR' to specify a working directory. Defaults to '$(DIR)'."
	@echo "Set 'VERBOSE' to '-v' or '-vv' to increase verbosity."
	@echo ""
	@echo "Example:"
	@echo ""
	@echo "    PACKAGE=rpm BRANCH=c8s VERBOSE=-vv make convert"

# clean before running the convert, so that cloning works
convert: clean
	git clone https://git.centos.org/rpms/$(PACKAGE).git $(DIR)/rpms/$(PACKAGE)
	./dist2src.py $(VERBOSE) convert $(DIR)/rpms/$(PACKAGE):$(BRANCH) $(DIR)/src/$(PACKAGE):$(BRANCH)
	git -C $(DIR)/src/$(PACKAGE) log --oneline $(BRANCH)

convert-fb: clean
	git clone https://github.com/facebookincubator/rpm-backports.git
	pushd rpm-backports
#	./dist2src.py $(VERBOSE) convert rpm-backports/rpms/$(PACKAGE):master rpm-backports/src/$(PACKAGE):master
	../dist2src.py $(VERBOSE) checkout --orphan src/$(PACKAGE) master
	../dist2src.py $(VERBOSE) get-archive --no-sources-sh rpms/$(PACKAGE)
	../dist2src.py $(VERBOSE) extract-archive rpms/$(PACKAGE) src/$(PACKAGE)
	../dist2src.py $(VERBOSE) copy-spec rpms/$(PACKAGE) src/$(PACKAGE)
	../dist2src.py $(VERBOSE) copy-patches rpms/$(PACKAGE) src/$(PACKAGE)
	../dist2src.py $(VERBOSE) apply-patches src/$(PACKAGE)

	git -C rpm-backports/src/$(PACKAGE) log --oneline

clean:
	rm -rf $(DIR)/
