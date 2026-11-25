pipeline {
    agent {
        docker {
            image 'python:3.13-slim'
            args '-u root --shm-size=1g'
            reuseNode true
        }
    }

    options {
        timestamps()
        timeout(time: 90, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    parameters {
        choice(name: 'TEST_ENV', choices: ['dev', 'test'], description: 'Environment profile in config.yml')
        choice(name: 'SUITE', choices: ['all', 'api', 'ui', 'perf'], description: 'Test layer to run')
        string(name: 'MEMBER_API_URL', defaultValue: 'http://127.0.0.1:8085', description: 'Member API base url')
        string(name: 'ADMIN_API_URL', defaultValue: 'http://127.0.0.1:8080', description: 'Admin API base url')
        string(name: 'MEMBER_UI_URL', defaultValue: 'http://127.0.0.1:5174', description: 'Member H5 base url')
        string(name: 'ADMIN_UI_URL', defaultValue: 'http://127.0.0.1:5173', description: 'Admin SPA base url')
        string(name: 'API_WORKERS', defaultValue: '1', description: 'pytest-xdist workers, 1 means sequential')
        string(name: 'CONFIG_CREDENTIAL_ID', defaultValue: 'mall-test-config', description: 'Jenkins file credential that stores config.yml')
        booleanParam(name: 'RUN_PERF_SMOKE', defaultValue: false, description: 'Run a 1-minute locust smoke after tests')
        string(name: 'PERF_USERS', defaultValue: '10', description: 'Locust users for the smoke run')
        string(name: 'PERF_DURATION', defaultValue: '1m', description: 'Locust duration for the smoke run')
    }

    environment {
        TEST_ENV = "${params.TEST_ENV}"
        MEMBER_URL = "${params.MEMBER_API_URL}"
        ADMIN_URL = "${params.ADMIN_API_URL}"
        MALL_MEMBER_URL = "${params.MEMBER_UI_URL}"
        MALL_ADMIN_URL = "${params.ADMIN_UI_URL}"
        MALL_UI_HEADLESS = 'true'
        API_WORKERS = "${params.API_WORKERS}"
        PYTHONUNBUFFERED = '1'
        PLAYWRIGHT_BROWSERS_PATH = "${WORKSPACE}/.playwright-browsers"
        ALLURE_RESULTS = 'reports/allure-results'
        PYTEST_COMMON = '-o addopts="" -v --tb=short --strict-markers --import-mode=importlib --maxfail=0'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare') {
            steps {
                sh '''
                    set -e
                    apt-get update
                    apt-get install -y --no-install-recommends curl
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m playwright install --with-deps chromium
                '''
            }
        }

        stage('Apply Config') {
            steps {
                withCredentials([file(credentialsId: params.CONFIG_CREDENTIAL_ID, variable: 'MALL_CONFIG_FILE')]) {
                    sh '''
                        set -e
                        mkdir -p reports/allure-results
                        cp "$MALL_CONFIG_FILE" common/config/config.yml
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    set -e
                    for url in "$MEMBER_URL" "$ADMIN_URL" "$MALL_MEMBER_URL" "$MALL_ADMIN_URL"; do
                        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || true)
                        if [ "$code" = "000" ]; then
                            echo "unreachable: $url"
                            exit 1
                        fi
                        echo "ok($code): $url"
                    done
                '''
            }
        }

        stage('API Test') {
            when {
                expression { params.SUITE == 'all' || params.SUITE == 'api' }
            }
            steps {
                sh '''
                    set -e
                    WORKERS=""
                    if [ "$API_WORKERS" -gt 1 ]; then
                        WORKERS="-n $API_WORKERS"
                    fi
                    pytest api/testcases $PYTEST_COMMON $WORKERS \
                        --html=reports/api_report.html --self-contained-html \
                        --alluredir="$ALLURE_RESULTS"
                '''
            }
        }

        stage('UI Test') {
            when {
                expression { params.SUITE == 'all' || params.SUITE == 'ui' }
            }
            steps {
                sh '''
                    set -e
                    pytest ui/testcases $PYTEST_COMMON \
                        --html=reports/ui_report.html --self-contained-html \
                        --alluredir="$ALLURE_RESULTS"
                '''
            }
        }

        stage('Performance Smoke') {
            when {
                expression { params.RUN_PERF_SMOKE || params.SUITE == 'perf' }
            }
            steps {
                sh '''
                    set -e
                    locust -f performance/locustfile.py --headless \
                        -u "$PERF_USERS" -r 2 -t "$PERF_DURATION" \
                        --host "$MEMBER_URL" \
                        --csv reports/locust --only-summary
                '''
            }
        }
    }

    post {
        always {
            allure includeProperties: true, jdk: '', results: [[path: 'reports/allure-results']]
            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'api_report.html,ui_report.html',
                reportName: 'Pytest HTML'
            ])
            archiveArtifacts artifacts: 'reports/locust*.csv, metrics_output/**', allowEmptyArchive: true
        }
        success {
            echo 'Mall automation finished successfully'
        }
        failure {
            echo 'Mall automation has failing tests, please check the Allure report'
        }
        cleanup {
            cleanWs()
        }
    }
}
