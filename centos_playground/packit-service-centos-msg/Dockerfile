FROM fedora:31

ENV LANG=en_US.UTF-8 \
    ANSIBLE_STDOUT_CALLBACK=debug \
    USER=packit \
    HOME=/home/packit

RUN dnf install -y ansible python3-pip

COPY files/install-deps.yaml /src/files/
RUN cd /src/ \
    && ansible-playbook -vv -c local -i localhost, files/install-deps.yaml \
    && dnf clean all

COPY setup.py setup.cfg files/recipe.yaml /src/

COPY .git /src/.git
COPY packit_service_centos_msg/ /src/packit_service_centos_msg/

RUN cd /src/ \
    && ansible-playbook -vv -c local -i localhost, recipe.yaml \
    && rm -rf /src/

CMD ["listen-to-centos-messaging"]
