"""
Tests for Docker build and configuration validation.
"""

import os
import pytest
import subprocess
from pathlib import Path


class TestDockerBuild:
    """Test Docker build process and configuration."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_dockerfile_exists(self, project_root):
        """Test that Dockerfile exists."""
        dockerfile = project_root / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile not found"
    
    def test_dockerignore_exists(self, project_root):
        """Test that .dockerignore exists (optional but recommended)."""
        dockerignore = project_root / ".dockerignore"
        # This is a soft check - it's recommended but not required
        if dockerignore.exists():
            assert dockerignore.is_file()
    
    def test_dockerfile_syntax(self, project_root):
        """Test Dockerfile syntax is valid."""
        dockerfile = project_root / "Dockerfile"
        content = dockerfile.read_text()
        
        # Check for required stages
        assert "FROM python" in content, "Dockerfile should use Python base image"
        assert "WORKDIR" in content, "Dockerfile should set WORKDIR"
        assert "COPY" in content, "Dockerfile should copy files"
        
        # Check for multi-stage build
        assert "as builder" in content or "as production" in content, \
            "Dockerfile should use multi-stage build"
    
    def test_dockerfile_has_healthcheck(self, project_root):
        """Test that Dockerfile includes health check."""
        dockerfile = project_root / "Dockerfile"
        content = dockerfile.read_text()
        
        assert "HEALTHCHECK" in content, "Dockerfile should include HEALTHCHECK"
    
    def test_dockerfile_runs_as_non_root(self, project_root):
        """Test that Dockerfile creates and uses non-root user."""
        dockerfile = project_root / "Dockerfile"
        content = dockerfile.read_text()
        
        # Check for user creation and switching
        assert "useradd" in content or "adduser" in content, \
            "Dockerfile should create non-root user"
        assert "USER" in content, "Dockerfile should switch to non-root user"
    
    def test_docker_compose_exists(self, project_root):
        """Test that docker-compose.yml exists."""
        docker_compose = project_root / "docker-compose.yml"
        assert docker_compose.exists(), "docker-compose.yml not found"
    
    def test_docker_compose_syntax(self, project_root):
        """Test docker-compose.yml syntax."""
        docker_compose = project_root / "docker-compose.yml"
        content = docker_compose.read_text()
        
        # Check for required services
        assert "services:" in content, "docker-compose.yml should define services"
        assert "api:" in content, "docker-compose.yml should include API service"
        
        # Check for volumes and networks
        assert "volumes:" in content, "docker-compose.yml should define volumes"
        assert "networks:" in content, "docker-compose.yml should define networks"
    
    def test_docker_compose_has_health_checks(self, project_root):
        """Test that docker-compose services have health checks."""
        docker_compose = project_root / "docker-compose.yml"
        content = docker_compose.read_text()
        
        assert "healthcheck:" in content, \
            "docker-compose.yml should include health checks"
    
    @pytest.mark.skipif(
        subprocess.run(["which", "docker"], capture_output=True).returncode != 0,
        reason="Docker not installed"
    )
    def test_docker_build_command(self, project_root):
        """Test that Docker build command works (if Docker is available)."""
        # This is a dry-run test - just check the command syntax
        result = subprocess.run(
            ["docker", "build", "--help"],
            capture_output=True,
            cwd=project_root
        )
        assert result.returncode == 0, "Docker build command should be available"
    
    def test_nginx_config_exists(self, project_root):
        """Test that nginx configuration exists."""
        nginx_conf = project_root / "nginx.conf"
        assert nginx_conf.exists(), "nginx.conf not found"
    
    def test_nginx_config_syntax(self, project_root):
        """Test nginx configuration syntax."""
        nginx_conf = project_root / "nginx.conf"
        content = nginx_conf.read_text()
        
        # Check for required sections
        assert "upstream" in content, "nginx.conf should define upstream servers"
        assert "server" in content, "nginx.conf should define server blocks"
        assert "location" in content, "nginx.conf should define location blocks"
    
    def test_nginx_config_has_ssl_support(self, project_root):
        """Test that nginx config has SSL configuration."""
        nginx_conf = project_root / "nginx.conf"
        content = nginx_conf.read_text()
        
        # SSL should be configured or at least commented out for future use
        assert "ssl" in content.lower() or "443" in content, \
            "nginx.conf should have SSL configuration or placeholders"
    
    def test_environment_template_exists(self, project_root):
        """Test that production environment template exists."""
        env_template = project_root / ".env.production.template"
        assert env_template.exists(), ".env.production.template not found"
    
    def test_environment_template_complete(self, project_root):
        """Test that environment template has all required variables."""
        env_template = project_root / ".env.production.template"
        content = env_template.read_text()
        
        required_vars = [
            "APP_NAME",
            "DATABASE_URL",
            "REDIS_URL",
            "AZURE_OPENAI_ENDPOINT",
            "SECRET_KEY"
        ]
        
        for var in required_vars:
            assert var in content, f"Environment template should include {var}"


class TestDockerSecurity:
    """Test Docker security configurations."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_dockerfile_no_secrets(self, project_root):
        """Test that Dockerfile doesn't contain hardcoded secrets."""
        dockerfile = project_root / "Dockerfile"
        content = dockerfile.read_text().lower()
        
        # Check for common secret patterns
        dangerous_patterns = ["password=", "api_key=", "secret="]
        for pattern in dangerous_patterns:
            assert pattern not in content, \
                f"Dockerfile should not contain hardcoded {pattern}"
    
    def test_docker_compose_uses_env_vars(self, project_root):
        """Test that docker-compose uses environment variables for secrets."""
        docker_compose = project_root / "docker-compose.yml"
        content = docker_compose.read_text()
        
        # Should use ${} syntax for environment variables
        assert "${" in content and "}" in content, \
            "docker-compose.yml should use environment variables"
    
    def test_no_root_user_in_production(self, project_root):
        """Test that production stage doesn't run as root."""
        dockerfile = project_root / "Dockerfile"
        content = dockerfile.read_text()
        
        # Find production stage and check for USER directive
        lines = content.split('\n')
        in_production = False
        has_user_directive = False
        
        for line in lines:
            if 'as production' in line.lower():
                in_production = True
            if in_production and line.strip().startswith('USER'):
                has_user_directive = True
                user = line.split()[1]
                assert user.lower() != 'root', \
                    "Production stage should not run as root user"
        
        assert has_user_directive, \
            "Production stage should have USER directive for non-root user"
