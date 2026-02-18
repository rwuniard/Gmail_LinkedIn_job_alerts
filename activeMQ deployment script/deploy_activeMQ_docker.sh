docker pull apache/activemq-artemis
docker run -d --name activemq-artemis -p 61616:61616 -p 8161:8161 apache/activemq-artemis