"""
Tests for deployment scripts validation.
"""

import os
import pytest
import stat
from pathlib import Path


class TestDeploymentScripts:
    """Test deployment scripts and configurations."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_deploy_script_exists(self, project_root):
        """Test that deploy.sh script exists."""
        deploy_script = project_root / "scripts" / "deploy.sh"
        assert deploy_script.exists(), "deploy.sh script not found"
    
    def test_deploy_script_is_executable(self, project_root):
        """Test that deploy.sh is executable."""
        deploy_script = project_root / "scripts" / "deploy.sh"
        if deploy_script.exists():
            file_stat = deploy_script.stat()
            # Check if file has execute permission
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
            assert is_executable, "deploy.sh should be executable"
    
    def test_deploy_script_has_shebang(self, project_root):
        """Test that deploy.sh has proper shebang."""
        deploy_script = project_root / "scripts" / "deploy.sh"
        if deploy_script.exists():
            content = deploy_script.read_text()
            assert content.startswith("#!/bin/bash"), \
                "deploy.sh should start with #!/bin/bash"
    
    def test_deploy_script_has_error_handling(self, project_root):
        """Test that deploy.sh has error handling."""
        deploy_script = project_root / "scripts" / "deploy.sh"
        if deploy_script.exists():
            content = deploy_script.read_text()
            
            # Check for set -e (exit on error)
            assert "set -e" in content, "deploy.sh should use 'set -e'"
    
    def test_smoke_tests_script_exists(self, project_root):
        """Test that smoke-tests.sh script exists."""
        smoke_tests = project_root / "scripts" / "smoke-tests.sh"
        assert smoke_tests.exists(), "smoke-tests.sh script not found"
    
    def test_smoke_tests_script_is_executable(self, project_root):
        """Test that smoke-tests.sh is executable."""
        smoke_tests = project_root / "scripts" / "smoke-tests.sh"
        if smoke_tests.exists():
            file_stat = smoke_tests.stat()
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
            assert is_executable, "smoke-tests.sh should be executable"
    
    def test_smoke_tests_validates_health(self, project_root):
        """Test that smoke tests check health endpoint."""
        smoke_tests = project_root / "scripts" / "smoke-tests.sh"
        if smoke_tests.exists():
            content = smoke_tests.read_text()
            assert "/health" in content, \
                "smoke-tests.sh should check /health endpoint"
    
    def test_deployment_directories_exist(self, project_root):
        """Test that deployment directories exist."""
        deployment_dir = project_root / "deployment"
        assert deployment_dir.exists(), "deployment directory not found"
        
        # Check for SQL directory
        sql_dir = deployment_dir / "sql"
        assert sql_dir.exists(), "deployment/sql directory not found"
    
    def test_sql_init_script_exists(self, project_root):
        """Test that SQL initialization script exists."""
        init_sql = project_root / "deployment" / "sql" / "init.sql"
        assert init_sql.exists(), "init.sql script not found"
    
    def test_sql_init_creates_tables(self, project_root):
        """Test that SQL init script creates necessary tables."""
        init_sql = project_root / "deployment" / "sql" / "init.sql"
        if init_sql.exists():
            content = init_sql.read_text()
            
            # Check for table creation
            assert "CREATE TABLE" in content, \
                "init.sql should create tables"
            
            # Check for important tables
            important_tables = ["users", "emails", "tasks"]
            for table in important_tables:
                assert table in content.lower(), \
                    f"init.sql should create {table} table"
    
    def test_sql_init_creates_indexes(self, project_root):
        """Test that SQL init script creates indexes."""
        init_sql = project_root / "deployment" / "sql" / "init.sql"
        if init_sql.exists():
            content = init_sql.read_text()
            
            assert "CREATE INDEX" in content, \
                "init.sql should create indexes for performance"


class TestKubernetesManifests:
    """Test Kubernetes deployment manifests."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_k8s_directory_exists(self, project_root):
        """Test that k8s directory exists."""
        k8s_dir = project_root / "k8s"
        assert k8s_dir.exists(), "k8s directory not found"
    
    def test_k8s_production_manifests_exist(self, project_root):
        """Test that production Kubernetes manifests exist."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        assert prod_manifest.exists(), \
            "k8s/production/deployment.yaml not found"
    
    def test_k8s_staging_manifests_exist(self, project_root):
        """Test that staging Kubernetes manifests exist."""
        staging_manifest = project_root / "k8s" / "staging" / "deployment.yaml"
        assert staging_manifest.exists(), \
            "k8s/staging/deployment.yaml not found"
    
    def test_k8s_production_manifest_syntax(self, project_root):
        """Test production Kubernetes manifest syntax."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        if prod_manifest.exists():
            content = prod_manifest.read_text()
            
            # Check for required Kubernetes resources
            assert "apiVersion:" in content, \
                "K8s manifest should have apiVersion"
            assert "kind: Deployment" in content, \
                "K8s manifest should define Deployment"
            assert "kind: Service" in content, \
                "K8s manifest should define Service"
    
    def test_k8s_production_has_resource_limits(self, project_root):
        """Test that production manifests define resource limits."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        if prod_manifest.exists():
            content = prod_manifest.read_text()
            
            assert "resources:" in content, \
                "K8s manifest should define resources"
            assert "limits:" in content, \
                "K8s manifest should define resource limits"
            assert "requests:" in content, \
                "K8s manifest should define resource requests"
    
    def test_k8s_production_has_health_checks(self, project_root):
        """Test that production manifests include health checks."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        if prod_manifest.exists():
            content = prod_manifest.read_text()
            
            assert "livenessProbe:" in content, \
                "K8s manifest should include livenessProbe"
            assert "readinessProbe:" in content, \
                "K8s manifest should include readinessProbe"
    
    def test_k8s_production_uses_secrets(self, project_root):
        """Test that production manifests use secrets for sensitive data."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        if prod_manifest.exists():
            content = prod_manifest.read_text()
            
            # Should use secretKeyRef for sensitive data
            assert "secretKeyRef:" in content, \
                "K8s manifest should use secrets for sensitive data"
    
    def test_k8s_production_has_autoscaling(self, project_root):
        """Test that production has autoscaling configuration."""
        prod_manifest = project_root / "k8s" / "production" / "deployment.yaml"
        if prod_manifest.exists():
            content = prod_manifest.read_text()
            
            # Check for HPA or autoscaling configuration
            assert "HorizontalPodAutoscaler" in content or \
                   "autoscaling" in content.lower(), \
                "Production should have autoscaling configured"


class TestCICDPipeline:
    """Test CI/CD pipeline configuration."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_github_workflows_directory_exists(self, project_root):
        """Test that GitHub workflows directory exists."""
        workflows_dir = project_root / ".github" / "workflows"
        assert workflows_dir.exists(), ".github/workflows directory not found"
    
    def test_cicd_workflow_exists(self, project_root):
        """Test that CI/CD workflow file exists."""
        cicd_workflow = project_root / ".github" / "workflows" / "ci-cd.yml"
        assert cicd_workflow.exists(), "ci-cd.yml workflow not found"
    
    def test_cicd_workflow_has_test_job(self, project_root):
        """Test that CI/CD workflow includes test job."""
        cicd_workflow = project_root / ".github" / "workflows" / "ci-cd.yml"
        if cicd_workflow.exists():
            content = cicd_workflow.read_text()
            
            assert "test" in content.lower(), \
                "CI/CD workflow should include test job"
    
    def test_cicd_workflow_has_build_job(self, project_root):
        """Test that CI/CD workflow includes build job."""
        cicd_workflow = project_root / ".github" / "workflows" / "ci-cd.yml"
        if cicd_workflow.exists():
            content = cicd_workflow.read_text()
            
            assert "build" in content.lower(), \
                "CI/CD workflow should include build job"
    
    def test_cicd_workflow_has_deploy_job(self, project_root):
        """Test that CI/CD workflow includes deploy job."""
        cicd_workflow = project_root / ".github" / "workflows" / "ci-cd.yml"
        if cicd_workflow.exists():
            content = cicd_workflow.read_text()
            
            assert "deploy" in content.lower(), \
                "CI/CD workflow should include deploy job"
    
    def test_cicd_workflow_has_docker_build(self, project_root):
        """Test that CI/CD workflow builds Docker images."""
        cicd_workflow = project_root / ".github" / "workflows" / "ci-cd.yml"
        if cicd_workflow.exists():
            content = cicd_workflow.read_text()
            
            assert "docker" in content.lower(), \
                "CI/CD workflow should build Docker images"
