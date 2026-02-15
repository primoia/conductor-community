# Migration to Centralized Infrastructure - conductor-community

## Migration Date
November 23, 2024

## Overview
The conductor-community service has been migrated from a standalone docker-compose setup with local MongoDB to a centralized infrastructure model. This migration removes the local MongoDB instance, allowing the conductor services to connect to a centralized MongoDB if available.

## What Changed

### MongoDB Configuration
- **Before**: Local MongoDB instance (conductor-mongodb:27017)
- **After**: Optional centralized MongoDB (primoia-mongodb if available)
- **Note**: Local MongoDB can still be used; this configuration provides flexibility

### Service Structure
- **Before**: Conductor API, Gateway, Web, and MongoDB all defined locally
- **After**: Conductor API, Gateway, Web with optional centralized MongoDB connection

### Network Configuration
- **Before**: Custom conductor-network
- **After**: Docker bridge network (primoia-network) with extra_hosts for centralized MongoDB

### Services Modified
- conductor-api: API service with configuration files
- gateway: Web gateway service
- web: Web UI service
- Removed: mongodb service definition (can be added back if needed)

### Files Created

1. **.env.centralized**
   - New environment configuration file for centralized infrastructure
   - Contains MongoDB configuration variables
   - Contains API and gateway endpoint URLs
   - Flexibility for using centralized or standalone MongoDB

2. **docker-compose.centralized.yml**
   - New docker-compose configuration without local MongoDB
   - Services use primoia-network bridge network
   - Includes extra_hosts for optional centralized MongoDB
   - All Conductor services working together

## Configuration Files Reference

### Environment Variables (.env.centralized)
```
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=<MONGO_PASSWORD>
MONGO_INITDB_DATABASE=conductor
CONDUCTOR_API_URL=http://conductor-api:8000
CONDUCTOR_GATEWAY_URL=http://gateway:8080
CONDUCTOR_WEB_URL=http://web:80
```

### Docker Compose Changes
- Removed: mongodb service definition (optional to restore)
- Updated: Network configuration to use bridge network
- Added: extra_hosts for optional centralized MongoDB
- Maintained: All Conductor service configurations
- Preserved: Configuration file volume mounts

## Deployment Instructions

### Prerequisites
Choose one of the following:
1. **Option A**: Use centralized MongoDB (if available)
   - Ensure MongoDB is running at primoia-mongodb
   - Update conductor config files to connect to centralized instance

2. **Option B**: Restore local MongoDB
   - If centralized MongoDB is not available
   - Use original docker-compose.yml and restore MongoDB service

### Deployment Steps
1. Set environment variables from .env.centralized:
   ```bash
   export $(cat .env.centralized | xargs)
   ```

2. Verify configuration files exist:
   ```bash
   ls -la ./config/conductor/.env
   ls -la ./config/conductor/config.yaml
   ls -la ./config/gateway/.env
   ls -la ./config/gateway/config.yaml
   ```

3. Start services using centralized compose file:
   ```bash
   docker-compose -f docker-compose.centralized.yml up -d
   ```

4. Verify services are running:
   ```bash
   docker-compose -f docker-compose.centralized.yml ps
   ```

5. Access the services:
   - Conductor API: http://localhost:3000
   - Conductor Gateway: http://localhost:5006
   - Conductor Web UI: http://localhost:8080

## MongoDB Configuration

### Option 1: Use Centralized MongoDB
If a centralized MongoDB instance is available:
1. Update conductor config files to point to primoia-mongodb
2. Ensure network connectivity to centralized MongoDB
3. Verify database permissions and authentication

### Option 2: Use Local MongoDB
If using local MongoDB:
1. Restore MongoDB service from original docker-compose.yml
2. Or start MongoDB separately on port 27017
3. Update conductor config to use local MongoDB

### Option 3: Hybrid Approach
Run MongoDB locally but use centralized infrastructure for other services:
1. Start MongoDB from original compose: `docker-compose up -d mongodb`
2. Run Conductor services: `docker-compose -f docker-compose.centralized.yml up -d`
3. Ensure services can communicate

## Data Migration
If migrating from existing Conductor instance:
1. Export existing MongoDB data:
   ```bash
   mongodump --out=/path/to/backup
   ```

2. Restore to new MongoDB:
   ```bash
   mongorestore --archive=/path/to/backup
   ```

3. Verify data integrity in Conductor UI

## Backup Strategy
- MongoDB backups: Depends on chosen setup
- Conductor configurations: Persisted in ./config volumes
- Workflow definitions: Stored in MongoDB
- Conductor state: Stored in MongoDB

## Monitoring and Logging
- Monitor Conductor API health endpoint
- Check Gateway request rates and latency
- Monitor Conductor workflow execution
- Aggregate logs from conductor-api, gateway, and web services
- Track MongoDB connection status

## Configuration Files
Ensure these files are properly configured:
- `./config/conductor/.env`: Conductor API environment
- `./config/conductor/config.yaml`: Conductor API configuration
- `./config/gateway/.env`: Gateway environment
- `./config/gateway/config.yaml`: Gateway configuration

## Conductor Features
The centralized setup maintains full access to:
- Workflow definitions and execution
- Distributed task orchestration
- Conductor UI for workflow management
- API endpoints for integration
- Event handling and webhooks

## Scaling Considerations
- Multiple Conductor instances can share same MongoDB
- Gateway can be scaled behind a load balancer
- API instances need shared MongoDB backend
- Consider MongoDB replication for high availability
- Implement connection pooling for scalability

## Rollback Procedure
If needed to rollback to standalone setup with local MongoDB:
1. Stop services: `docker-compose -f docker-compose.centralized.yml down`
2. Use original docker-compose.yml: `docker-compose up -d`
3. Verify MongoDB data is intact

## Known Limitations
1. MongoDB is not included in centralized infrastructure definition
2. Must choose between local or centralized MongoDB
3. Configuration files must be manually maintained
4. Conductor version depends on image tags

## Performance Considerations
1. Local MongoDB: Better latency, no network overhead
2. Centralized MongoDB: Shared resources, potential contention
3. Database choice impacts workflow execution performance
4. Consider MongoDB indexing for large datasets

## Integration with Other Services
- API Gateway can route to Conductor Gateway
- Other services can call Conductor API
- Workflow definitions can trigger other microservices
- Message queue integration for async workflows

## Next Steps
1. Choose MongoDB deployment option (local or centralized)
2. Configure conductor config files as needed
3. Test Conductor API endpoints
4. Create and test workflow definitions
5. Monitor Conductor performance metrics
6. Validate integration with other customer services
7. Set up backup and recovery procedures
8. Configure monitoring and alerting

## Contact
For migration support or issues, contact the infrastructure team.

## Checklist
- [x] Created .env.centralized
- [x] Created docker-compose.centralized.yml
- [x] Documented MongoDB configuration options
- [x] Documented migration process
- [ ] MongoDB deployment option selected (local or centralized)
- [ ] Configuration files verified
- [ ] Conductor services tested
- [ ] MongoDB data integrity validated
- [ ] Workflow definitions migrated
- [ ] API endpoints tested
- [ ] Integration with other services validated
- [ ] Backup procedures established
- [ ] Monitoring and alerting configured
