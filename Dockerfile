FROM compss/compss-ubuntu16:stable

MAINTAINER COMPSs Support <support-compss@bsc.es>


# Enable ssh to localhost
RUN pip3 install codecov coverage flake8 matplotlib && \
    yes yes | ssh-keygen -f /root/.ssh/id_rsa -t rsa -N '' > /dev/null && \
    cat /root/.ssh/id_rsa.pub > /root/.ssh/authorized_keys 

COPY dislib dislib/dislib
COPY examples dislib/examples
COPY tests dislib/tests
COPY run_tests.sh /dislib/
COPY run_coverage.sh /dislib/
COPY bin/cfg.sh /
COPY bin/generate_project.sh /
COPY bin/generate_resources.sh /

ENV PATH=$PATH:/opt/COMPSs/Runtime/scripts/user:/opt/COMPSs/Bindings/c/bin
ENV CLASSPATH=$CLASSPATH:/opt/COMPSs/Runtime/compss-engine.jar
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/
ENV PYTHONPATH=$PYTHONPATH:/dislib
#ENV MPI_HOME=/usr/lib64/openmpi
#ENV LD_LIBRARY_PATH=/usr/lib64/openmpi/lib

