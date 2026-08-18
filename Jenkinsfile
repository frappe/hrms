pipeline {
    agent any
    options { timeout(time: 15, unit: 'MINUTES') }
    environment {
        COMPOSE_FILE = '/opt/app/hrms/docker/docker-compose.yml'
        PROJECT = 'docker'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Redeploy dev stack') {
            steps {
                sh 'docker compose -f $COMPOSE_FILE -p $PROJECT down'
                sh 'docker compose -f $COMPOSE_FILE -p $PROJECT up -d --build'
            }
        }
        stage('Health check') {
            steps {
                sh '''
                  for i in $(seq 1 20); do
                    if curl -sf http://localhost:8000 > /dev/null; then
                      echo "hrms is up"; exit 0
                    fi
                    sleep 15
                  done
                  echo "hrms did not become healthy in time"; exit 1
                '''
            }
        }
    }
}
