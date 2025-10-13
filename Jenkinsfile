pipeline {
    agent any

    triggers {
        // Run every day at 2 AM
        cron('H 2 * * *')
    }

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

                    # Handle venv permissions or recreate it if needed
                    if [ -d "$VENV" ] && [ ! -w "$VENV" ]; then
                        echo "Existing venv has permission issues. Removing..."
                        rm -rf "$VENV"
                    fi

                    if [ ! -d "$VENV" ]; then
                        echo "Creating a new virtual environment..."
                        python3 -m venv "$VENV"
                    fi

                    # Install dependencies
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
        stage('Ping Test (8.8.8.8) Webserver') {
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
            emailext (
                to: 'aravindh.goutham.mahe@gmail.com',
                subject: "SUCCESS: Network Automation Daily Build #${env.BUILD_NUMBER}",
                body: """
                    <h2>Network Automation Daily Report</h2>
                    <p>All tests passed successfully.</p>
                    <ul>
                        <li><b>Job:</b> ${env.JOB_NAME}</li>
                        <li><b>Build:</b> #${env.BUILD_NUMBER}</li>
                        <li><b>Date:</b> ${new Date()}</li>
                    </ul>
                    <p><a href="${env.BUILD_URL}">View full build logs in Jenkins</a></p>
                """,
                mimeType: 'text/html'
            )
        }

        failure {
            echo 'Some network or template tests failed!'
            emailext (
                to: 'aravindh.goutham.mahe@gmail.com',
                subject: "FAILED: Network Automation Daily Build #${env.BUILD_NUMBER}",
                body: """
                    <h2>Network Automation Daily Report</h2>
                    <p>One or more tests failed during the nightly build.</p>
                    <ul>
                        <li><b>Job:</b> ${env.JOB_NAME}</li>
                        <li><b>Build:</b> #${env.BUILD_NUMBER}</li>
                        <li><b>Date:</b> ${new Date()}</li>
                    </ul>
                    <p><a href="${env.BUILD_URL}">View detailed failure logs</a></p>
                """,
                mimeType: 'text/html'
            )
        }

        always {
            echo 'Pipeline execution complete.'
        }
    }
}


