.PHONY: usage check clean

PACKAGE ?= rpm
BRANCH ?= c8s
DIR ?= git.centos.org

usage:
	@echo "Run 'make check' to run the check or 'make clean' to clean up things."
	@echo ""
	@echo "Set 'PACKAGE' to pick a package from git.centos.org/rpms. Defaults to '$(PACKAGE)'."
	@echo "Set 'BRANCH' to select the branch to convert. Defaults to '$(BRANCH)'."
	@echo "Set 'DIR' to specify a working directory. Defaults to '$(DIR)'."
	@echo "Set 'VERBOSE' to '-v' or '-vv' to increase verbosity."
	@echo ""
	@echo "Example:"
	@echo ""
	@echo "    PACKAGE=rpm BRANCH=c8s VERBOSE=-vv make check"

# clean before running the check, so that cloning works
check: clean
	git clone https://git.centos.org/rpms/$(PACKAGE).git $(DIR)/rpms/$(PACKAGE)
	./dist2src.py $(VERBOSE) convert $(DIR)/rpms/$(PACKAGE):$(BRANCH) $(DIR)/src/$(PACKAGE):$(BRANCH)
	git -C $(DIR)/src/$(PACKAGE) log --oneline $(BRANCH)

clean:
	rm -rf $(DIR)/
