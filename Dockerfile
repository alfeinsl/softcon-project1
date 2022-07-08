FROM openjdk:8
EXPOSE 8080
ADD target/jenkins-docker-integratiom.jar jenkins-docker-integration.jar
ENTRYPOINT ["java","-jar","/jenkins-docker-integration,jar"]