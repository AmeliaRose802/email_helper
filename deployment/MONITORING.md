# Monitoring and Alerting Configuration

This document describes the monitoring and alerting setup for the Email Helper application.

## 🎯 Monitoring Strategy

### Key Metrics

#### Application Performance
- **Response Time**: API endpoint latency (target: <500ms p95)
- **Throughput**: Requests per second
- **Error Rate**: Failed requests / total requests (target: <1%)
- **Availability**: Uptime percentage (target: 99.9%)

#### Infrastructure
- **CPU Usage**: Server CPU utilization (alert: >80%)
- **Memory Usage**: Application memory consumption (alert: >85%)
- **Disk I/O**: Database read/write operations
- **Network**: Bandwidth usage and latency

#### Business Metrics
- **Email Processing**: Emails processed per hour
- **AI Classifications**: Classification accuracy
- **User Activity**: Active users and session duration
- **Background Jobs**: Job queue length and processing time

## 📊 Application Insights Configuration

### Custom Events

```python
# Backend telemetry examples
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

# Configure Application Insights
configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

tracer = trace.get_tracer(__name__)

# Track email processing
with tracer.start_as_current_span("email_processing") as span:
    span.set_attribute("email_count", email_count)
    span.set_attribute("classification_accuracy", accuracy)
    # Process emails
    
# Track AI requests
with tracer.start_as_current_span("ai_classification") as span:
    span.set_attribute("model", "gpt-4o")
    span.set_attribute("token_count", token_count)
    # Call AI service
```

### Alert Rules

#### Critical Alerts (Immediate Response)

1. **Application Down**
   - Condition: Health check fails for 2 consecutive minutes
   - Action: Page on-call engineer
   - Severity: Critical

2. **Database Connection Failure**
   - Condition: Database connection errors >5 in 5 minutes
   - Action: Page on-call engineer and database admin
   - Severity: Critical

3. **High Error Rate**
   - Condition: Error rate >5% for 5 minutes
   - Action: Alert DevOps team
   - Severity: Critical

#### Warning Alerts (Investigation Needed)

1. **High Response Time**
   - Condition: P95 response time >1000ms for 10 minutes
   - Action: Email DevOps team
   - Severity: Warning

2. **High CPU Usage**
   - Condition: CPU >80% for 15 minutes
   - Action: Email DevOps team, auto-scale if possible
   - Severity: Warning

3. **Memory Pressure**
   - Condition: Memory usage >85% for 10 minutes
   - Action: Email DevOps team
   - Severity: Warning

4. **Job Queue Backlog**
   - Condition: Queue length >100 jobs for 20 minutes
   - Action: Email DevOps team
   - Severity: Warning

## 🔔 Alert Configuration in Azure

### Using Azure CLI

```bash
# Create action group for notifications
az monitor action-group create \
  --name "email-helper-alerts" \
  --resource-group "email-helper-production-rg" \
  --short-name "eh-alerts" \
  --email-receiver name="DevOps Team" email="devops@example.com"

# Create metric alert for high error rate
az monitor metrics alert create \
  --name "high-error-rate" \
  --resource-group "email-helper-production-rg" \
  --scopes "/subscriptions/{sub-id}/resourceGroups/email-helper-production-rg/providers/Microsoft.Web/sites/email-helper-production-backend" \
  --condition "avg requests/failed > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action "email-helper-alerts"

# Create availability test
az monitor app-insights web-test create \
  --resource-group "email-helper-production-rg" \
  --name "backend-health-check" \
  --location "eastus" \
  --defined-web-test-name "Backend Health Check" \
  --kind "ping" \
  --frequency 300 \
  --timeout 30 \
  --retry-enabled true \
  --web-test-url "https://email-helper-production-backend.azurewebsites.net/health"
```

### Using Terraform

Add to `deployment/terraform/main.tf`:

```hcl
# Action Group
resource "azurerm_monitor_action_group" "alerts" {
  name                = "${local.resource_name_prefix}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "eh-alerts"

  email_receiver {
    name                    = "DevOps Team"
    email_address          = "devops@example.com"
    use_common_alert_schema = true
  }

  webhook_receiver {
    name        = "Slack"
    service_uri = var.slack_webhook_url
  }
}

# High Error Rate Alert
resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "${local.resource_name_prefix}-high-error-rate"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when error rate exceeds 5%"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 5
  }

  window_size        = "PT5M"
  frequency          = "PT1M"
  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }
}

# Availability Test
resource "azurerm_application_insights_web_test" "health_check" {
  name                    = "${local.resource_name_prefix}-health-check"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.main.id
  kind                    = "ping"
  frequency               = 300
  timeout                 = 30
  enabled                 = true
  retry_enabled           = true
  geo_locations           = ["us-va-ash-azr", "us-ca-sjc-azr"]

  configuration = <<XML
<WebTest Name="${local.resource_name_prefix}-health-check" Enabled="True" Timeout="30">
  <Items>
    <Request Method="GET" Version="1.1" Url="https://${azurerm_linux_web_app.backend.default_hostname}/health" ThinkTime="0" Timeout="30" ParseDependentRequests="False" FollowRedirects="True" />
  </Items>
  <ValidationRules>
    <ValidationRule Classname="Microsoft.VisualStudio.TestTools.WebTesting.Rules.ValidationRuleFindText" DisplayName="Find Text" Level="High" ExectuionOrder="BeforeDependents">
      <RuleParameters>
        <RuleParameter Name="FindText" Value="healthy" />
        <RuleParameter Name="IgnoreCase" Value="False" />
        <RuleParameter Name="UseRegularExpression" Value="False" />
        <RuleParameter Name="PassIfTextFound" Value="True" />
      </RuleParameters>
    </ValidationRule>
  </ValidationRules>
</WebTest>
XML
}
```

## 📈 Custom Dashboards

### Application Insights Dashboard

Create in Azure Portal or using ARM template:

```json
{
  "properties": {
    "lenses": {
      "0": {
        "order": 0,
        "parts": {
          "0": {
            "position": { "x": 0, "y": 0, "colSpan": 6, "rowSpan": 4 },
            "metadata": {
              "type": "Extension/AppInsightsExtension/PartType/AppMapGalPt",
              "inputs": [
                {
                  "name": "resourceId",
                  "value": "/subscriptions/{sub-id}/resourceGroups/email-helper-production-rg/providers/microsoft.insights/components/email-helper-production-appinsights"
                }
              ]
            }
          },
          "1": {
            "position": { "x": 6, "y": 0, "colSpan": 6, "rowSpan": 4 },
            "metadata": {
              "type": "Extension/AppInsightsExtension/PartType/PerformanceTrendGalPt",
              "inputs": [
                {
                  "name": "resourceId",
                  "value": "/subscriptions/{sub-id}/resourceGroups/email-helper-production-rg/providers/microsoft.insights/components/email-helper-production-appinsights"
                }
              ]
            }
          }
        }
      }
    }
  }
}
```

### Grafana Integration (Optional)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

## 🔍 Log Aggregation

### Structured Logging

```python
# backend/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
            
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
            
        return json.dumps(log_obj)

# Configure logger
logger = logging.getLogger("email_helper")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Log Queries

```kusto
// Application Insights Query Language (KQL) examples

// Top errors in last 24 hours
exceptions
| where timestamp > ago(24h)
| summarize count() by outerMessage, innermostMessage
| order by count_ desc
| take 10

// Slow requests
requests
| where timestamp > ago(1h)
| where duration > 1000
| project timestamp, name, url, duration, resultCode
| order by duration desc

// Failed requests by endpoint
requests
| where timestamp > ago(24h)
| where success == false
| summarize count() by name, resultCode
| order by count_ desc

// Custom events - email processing
customEvents
| where name == "email_processing"
| where timestamp > ago(24h)
| extend email_count = tolong(customDimensions.email_count)
| summarize 
    total_emails = sum(email_count),
    avg_per_batch = avg(email_count)
    by bin(timestamp, 1h)
```

## 🚨 Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P0 - Critical | Complete outage | 15 minutes | Application down, database unavailable |
| P1 - High | Major degradation | 30 minutes | High error rate, slow response times |
| P2 - Medium | Partial degradation | 2 hours | Non-critical feature broken, warning alerts |
| P3 - Low | Minor issues | 1 business day | Cosmetic issues, minor bugs |

### On-Call Rotation

```yaml
# PagerDuty schedule example
schedules:
  - name: "Email Helper On-Call"
    time_zone: "America/New_York"
    layers:
      - name: "Primary"
        start: "2024-01-01T00:00:00"
        rotation_virtual_start: "2024-01-01T00:00:00"
        rotation_turn_length_seconds: 604800  # 1 week
        users:
          - user: "engineer1@example.com"
          - user: "engineer2@example.com"
          - user: "engineer3@example.com"
```

### Runbooks

Location: `/deployment/runbooks/`

- `00-incident-response.md` - General incident response procedures
- `01-application-restart.md` - How to restart the application
- `02-database-issues.md` - Database troubleshooting
- `03-scaling-operations.md` - Manual scaling procedures
- `04-rollback-deployment.md` - How to rollback a deployment

## 📱 Notification Channels

### Email Alerts
- **Recipients**: devops@example.com
- **Format**: HTML with graphs and links
- **Frequency**: Immediate for critical, batched for warnings

### Slack Integration
```bash
# Create Slack incoming webhook
# Add webhook URL to alert action group
az monitor action-group create \
  --name "email-helper-slack" \
  --resource-group "email-helper-production-rg" \
  --webhook-receiver name="Slack" serviceUri="https://hooks.slack.com/services/..."
```

### SMS/Phone (Critical Only)
- **Recipients**: On-call engineer
- **Conditions**: P0 incidents only
- **Rate Limiting**: Max 5 per hour

## 🔒 Security Monitoring

### Failed Authentication Attempts
```kusto
customEvents
| where name == "failed_login"
| where timestamp > ago(1h)
| summarize attempts = count() by user = tostring(customDimensions.username), ip = tostring(customDimensions.ip_address)
| where attempts > 5
```

### Suspicious Activity
- Multiple failed login attempts
- Access from unusual locations
- Unusual API usage patterns
- Large data exports

## 📋 Regular Maintenance

### Daily
- Review error logs
- Check application health
- Monitor resource usage

### Weekly
- Review alert thresholds
- Analyze performance trends
- Check backup success

### Monthly
- Review and optimize alert rules
- Update monitoring dashboards
- Conduct incident post-mortems
- Review and update runbooks

## 🎓 Additional Resources

- [Azure Monitor Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/)
- [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [KQL Query Language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/)
