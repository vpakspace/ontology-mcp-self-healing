# Troubleshooting Guide

Common issues and solutions for the Self-Healing Ontology MCP Agent System.

## Schema Changes Not Detected

**Symptoms**: Schema changes made but not detected by monitor.

**Solutions**:
1. Check monitoring is enabled in config:
   ```yaml
   monitoring:
     enabled: true
     check_interval: 60
   ```

2. Verify database connection:
   ```bash
   python -c "from sqlalchemy import create_engine; engine = create_engine('your_connection_string'); print(engine.connect())"
   ```

3. Check logs for errors:
   ```bash
   tail -f logs/system.log
   ```

4. Ensure check interval is appropriate (lower = more frequent checks)

## Ontology Not Reloading

**Symptoms**: Schema changes detected but MCP server not updating.

**Solutions**:
1. Check auto-reload is enabled:
   ```yaml
   ontology:
     auto_reload: true
   ```

2. Verify ontology file is writable:
   ```bash
   ls -la ontologies/business_domain.owl
   chmod 644 ontologies/business_domain.owl
   ```

3. Check for file lock issues (if using Docker, check volume mounts)

4. Review healing logs:
   ```bash
   grep "healing" logs/audit.json | tail -20
   ```

## Claude API Errors

**Symptoms**: Healing fails with API errors.

**Solutions**:
1. Verify API key is set:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

2. Check API rate limits (Claude has rate limits)

3. Verify API key has correct permissions

4. Check network connectivity:
   ```bash
   curl https://api.anthropic.com/v1/messages
   ```

5. Review error messages in logs:
   ```bash
   grep "anthropic\|claude" logs/system.log | tail -20
   ```

## MCP Tools Not Generated

**Symptoms**: No tools available after starting server.

**Solutions**:
1. Verify ontology file exists and is valid:
   ```bash
   python -c "from owlready2 import get_ontology; ont = get_ontology('file://$(pwd)/ontologies/business_domain.owl').load(); print(list(ont.classes()))"
   ```

2. Check for `mapsToTable` and `mapsToColumn` annotations in ontology

3. Verify ontology file path in config:
   ```yaml
   ontology:
     main_file: ontologies/business_domain.owl
   ```

4. Check server logs for parsing errors

## Agent Queries Failing

**Symptoms**: Agents can't execute queries.

**Solutions**:
1. Verify MCP server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check agent has access to tools:
   ```python
   agent.get_available_tools()
   ```

3. Verify database connection is working

4. Check query syntax (test with direct MCP tool call)

## Docker Issues

**Symptoms**: Container won't start or crashes.

**Solutions**:
1. Check container logs:
   ```bash
   docker logs ontology-mcp
   ```

2. Verify environment variables:
   ```bash
   docker exec ontology-mcp env | grep ANTHROPIC
   ```

3. Check volume mounts:
   ```bash
   docker inspect ontology-mcp | grep Mounts
   ```

4. Verify image is built correctly:
   ```bash
   docker build -t ontology-mcp-self-healing .
   ```

## Database Connection Issues

**Symptoms**: Can't connect to database.

**Solutions**:
1. Verify connection string format:
   - SQLite: `sqlite:///./database.db`
   - PostgreSQL: `postgresql://user:pass@host:5432/dbname`

2. Test connection manually:
   ```python
   from sqlalchemy import create_engine
   engine = create_engine('your_connection_string')
   with engine.connect() as conn:
       print("Connected!")
   ```

3. Check firewall/network rules

4. Verify database credentials

## Performance Issues

**Symptoms**: Slow queries or high resource usage.

**Solutions**:
1. Enable query caching:
   ```yaml
   mcp_server:
     enable_caching: true
     cache_ttl: 300
   ```

2. Adjust connection pool size:
   ```yaml
   database:
     pool_size: 10
     max_overflow: 20
   ```

3. Increase monitoring interval (if too frequent):
   ```yaml
   monitoring:
     check_interval: 300  # 5 minutes instead of 60 seconds
   ```

4. Review slow query logs

## Permission Errors

**Symptoms**: File permission errors when writing logs or ontology.

**Solutions**:
1. Check file permissions:
   ```bash
   ls -la logs/ ontologies/
   ```

2. Fix permissions:
   ```bash
   chmod -R 755 logs/ ontologies/
   ```

3. If using Docker, check volume mount ownership

4. Run as correct user (not root in production)

## Getting Help

1. Check logs first: `logs/system.log` and `logs/audit.json`
2. Review configuration: `config/config.yaml`
3. Test individual components separately
4. Enable debug logging:
   ```yaml
   logging:
     level: DEBUG
   ```
5. Open an issue on GitHub with:
   - Error messages
   - Configuration (sanitized)
   - Log snippets
   - Steps to reproduce

## Common Error Messages

### "Ontology file not found"
- Verify path in config
- Check file exists
- Verify read permissions

### "Database connection failed"
- Check connection string
- Verify database is running
- Check network connectivity

### "No tools found"
- Check ontology has mappings
- Verify class definitions
- Check for parsing errors

### "Healing failed: Invalid triples"
- Check Claude API response
- Verify triple validation
- Review ontology format

### "Schema hash unchanged"
- Normal if no changes
- Check if changes were actually made
- Verify correct database is monitored
