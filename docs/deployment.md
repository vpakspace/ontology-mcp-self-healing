# Deployment Guide

## Production Deployment

This guide covers deploying the Self-Healing Ontology MCP Agent System in production environments.

## Prerequisites

- Python 3.10+ or Docker
- PostgreSQL or SQLite database
- Anthropic API key
- (Optional) Slack/Teams webhook URL

## Docker Deployment

### Basic Docker Run

```bash
docker run -d \
  --name ontology-mcp \
  -e ANTHROPIC_API_KEY=your_key_here \
  -e ALERT_WEBHOOK_URL=your_webhook_url \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/ontologies:/app/ontologies \
  -v $(pwd)/logs:/app/logs \
  -p 8000:8000 \
  ontology-mcp-self-healing
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ontology-mcp-self-healing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ontology-mcp
  template:
    metadata:
      labels:
        app: ontology-mcp
    spec:
      containers:
      - name: self-healing
        image: ontology-mcp-self-healing:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-secret
              key: api-key
        - name: ALERT_WEBHOOK_URL
          valueFrom:
            configMapKeyRef:
              name: config
              key: webhook-url
        volumeMounts:
        - name: ontologies
          mountPath: /app/ontologies
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: ontologies
        persistentVolumeClaim:
          claimName: ontologies-pvc
      - name: config
        configMap:
          name: config
      - name: logs
        emptyDir: {}
```

### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ontology-mcp-service
spec:
  selector:
    app: ontology-mcp
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: config
data:
  config.yaml: |
    database:
      connection_string: postgresql://user:pass@db:5432/dbname
    monitoring:
      check_interval: 60
    healing:
      auto_approve: false
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: anthropic-secret
type: Opaque
stringData:
  api-key: your_anthropic_api_key_here
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ontology-mcp-ingress
spec:
  rules:
  - host: ontology-mcp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ontology-mcp-service
            port:
              number: 8000
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ontology-mcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ontology-mcp-self-healing
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Helm Chart

Create a Helm chart for easier deployment:

```bash
helm create ontology-mcp
```

Key values to configure:
- `replicas`: Number of replicas
- `image.repository`: Docker image repository
- `image.tag`: Image tag
- `config.database.connectionString`: Database connection
- `secrets.anthropicApiKey`: Anthropic API key
- `ingress.enabled`: Enable ingress

## Environment Variables

Required:
- `ANTHROPIC_API_KEY`: Anthropic Claude API key

Optional:
- `ALERT_WEBHOOK_URL`: Webhook URL for alerts
- `DATABASE_URL`: Database connection string (overrides config)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Monitoring

### Health Checks

The system includes health check endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

### Logging

Logs are written to:
- `logs/system.log`: System logs
- `logs/audit.json`: Audit trail (JSON format)

View logs:
```bash
# Docker
docker logs ontology-mcp

# Kubernetes
kubectl logs -f deployment/ontology-mcp-self-healing
```

### Metrics

Key metrics to monitor:
- Schema change detection rate
- Healing success/failure rate
- MCP query latency
- Agent query success rate

## Backup and Recovery

### Backup Ontology Files

```bash
# Backup ontologies
tar -czf ontologies-backup-$(date +%Y%m%d).tar.gz ontologies/

# Backup database
pg_dump database_name > backup-$(date +%Y%m%d).sql
```

### Restore

```bash
# Restore ontologies
tar -xzf ontologies-backup-YYYYMMDD.tar.gz

# Restore database
psql database_name < backup-YYYYMMDD.sql
```

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:
- MCP server is stateless (can scale horizontally)
- Schema monitor should run as single instance or leader election
- Self-healing system should run as single instance

### Vertical Scaling

Increase resources for:
- Large ontology files
- High query volume
- Complex schema changes

## Security Best Practices

1. **API Keys**: Store in secrets management (K8s Secrets, Vault)
2. **Network**: Use private networks for database connections
3. **Access Control**: Implement API key authentication for MCP server
4. **Audit Logs**: Enable and monitor audit logs
5. **Updates**: Keep dependencies updated

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

## Production Checklist

- [ ] Database connection pool configured
- [ ] API keys stored in secrets
- [ ] Alert webhooks configured
- [ ] Health checks enabled
- [ ] Monitoring dashboards set up
- [ ] Backup strategy in place
- [ ] Log rotation configured
- [ ] Rate limiting configured (if needed)
- [ ] SSL/TLS enabled (if exposing externally)
- [ ] Disaster recovery plan documented
