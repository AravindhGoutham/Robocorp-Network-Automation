pipeline {
    agent any

    environment {
        PROJECT_DIR = "/home/student/Network-Automation"
        VENV = "${PROJECT_DIR}/venv"
    }

    stages {
        /* -------------------- Setup -------------------- */
        stage('Setup Environment') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    cd $PROJECT_DIR

                    if [ -d "$VENV" ] && [ ! -w "$VENV" ]; then
                        echo "Existing venv has permission issues. Removing..."
                        rm -rf "$VENV"
                    fi

                    if [ ! -d "$VENV" ]; then
                        echo "Creating a new virtual environment..."
                        python3 -m venv "$VENV"
                    fi

                    $VENV/bin/pip install --upgrade pip netmiko pyyaml jinja2
                '''
            }
        }

        /* -------------------- Jinja2 Template Validation -------------------- */
        stage('Jinja2 Template Validation') {
            steps {
                echo 'Validating Jinja2 templates for syntax and undefined variables...'
                sh '''
                    cd $PROJECT_DIR
                    $VENV/bin/python3 template_validation.py
                '''
            }
        }

        /* -------------------- Ping Test -------------------- */
        stage('Ping Test (8.8.8.8)') {
            steps {
                echo 'Running global connectivity tests...'
                sh '''
                    cd $PROJECT_DIR
                    $VENV/bin/python3 network_tests.py
                '''
            }
        }

        /* -------------------- Routing Health -------------------- */
        stage('Routing Health (OSPF, BGP, NMAS)') {
            steps {
                echo 'Running routing health checks...'
                sh '''
                    cd $PROJECT_DIR
                    $VENV/bin/python3 routing_healthcheck.py
                '''
            }
        }
    }

    /* -------------------- Post Actions -------------------- */
    post {
        success {
            echo 'All tests passed successfully!'
        }
        failure {
            echo 'Some network or template tests failed!'
        }
        always {
            echo 'Pipeline execution complete.'
        }
    }
}
