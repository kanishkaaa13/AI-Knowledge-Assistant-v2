# Production Deployment Checklist

Use this checklist before deploying to production to ensure everything is properly configured.

## Pre-Deployment

### Code Review
- [ ] All code has been reviewed
- [ ] No hardcoded secrets or credentials
- [ ] No debug statements or console.logs in production code
- [ ] All TODO comments addressed or documented
- [ ] Error handling is comprehensive
- [ ] Input validation is implemented
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection is enabled

### Environment Variables
- [ ] `JWT_SECRET_KEY` changed from default (min 32 characters)
- [ ] `FERNET_SECRET_KEY` changed from default (min 32 bytes)
- [ ] `DATABASE_URL` points to production database
- [ ] `BACKEND_CORS_ORIGINS` includes only production frontend URLs
- [ ] `APP_ENV` set to `production`
- [ ] `NEXT_PUBLIC_API_BASE_URL` set to production backend URL
- [ ] `OLLAMA_BASE_URL` configured correctly
- [ ] All sensitive variables are set in platform (not committed to git)

### Database
- [ ] PostgreSQL database created
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] SSL enabled for database connections
- [ ] Database indexes verified
- [ ] Foreign key constraints verified
- [ ] Cascade delete rules verified

### Security
- [ ] HTTPS enabled (automatic on Vercel/Render)
- [ ] Security headers configured:
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] Referrer-Policy: strict-origin-when-cross-origin
  - [ ] Permissions-Policy configured
  - [ ] Strict-Transport-Security (HSTS) enabled
- [ ] Rate limiting configured and tested
- [ ] Input sanitization implemented
- [ ] File upload validation implemented
- [ ] File encryption at rest enabled
- [ ] JWT tokens have appropriate expiration
- [ ] Refresh token rotation implemented
- [ ] API documentation disabled in production
- [ ] CORS configured to only allow trusted domains

### Performance
- [ ] Database connection pooling configured
- [ ] Response caching implemented where appropriate
- [ ] Static assets optimized
- [ ] Images compressed
- [ ] Lazy loading implemented
- [ ] Pagination implemented for large datasets
- [ ] Database queries optimized
- [ ] N+1 query issues resolved
- [ ] Background jobs configured for async tasks

### Monitoring & Logging
- [ ] Logging configured for production (INFO level)
- [ ] Error tracking setup (Sentry, LogRocket, or similar)
- [ ] Performance monitoring setup
- [ ] Database monitoring configured
- [ ] Application performance monitoring (APM) setup
- [ ] Log aggregation configured
- [ ] Alert rules configured for critical errors
- [ ] Uptime monitoring configured

### Testing
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end tests passing
- [ ] Load testing performed
- [ ] Security testing performed
- [ ] Manual testing completed:
  - [ ] User registration/login
  - [ ] Document upload
  - [ ] Chat functionality
  - [ ] File download
  - [ ] Conversation management
  - [ ] Analytics dashboard
  - [ ] Settings and preferences

## Deployment

### Backend (Render)
- [ ] Repository connected to Render
- [ ] `render.yaml` configuration reviewed
- [ ] Build command verified
- [ ] Start command verified
- [ ] Environment variables set
- [ ] Database linked
- [ ] Migrations run after deployment
- [ ] Health check endpoint accessible
- [ ] API documentation disabled (verify /docs returns 404)
- [ ] Static file serving configured
- [ ] Service is responding to requests

### Frontend (Vercel)
- [ ] Repository connected to Vercel
- [ ] `vercel.json` configuration reviewed
- [ ] Build command verified
- [ ] Environment variables set
- [ ] Custom domain configured (if applicable)
- [ ] Build successful
- [ ] Deployment successful
- [ ] Frontend accessible via HTTPS
- [ ] API calls working correctly
- [ ] All pages loading correctly

### Post-Deployment Verification
- [ ] Backend health check passing: `curl https://your-backend.onrender.com/health`
- [ ] Frontend loading correctly
- [ ] User can register/login
- [ ] User can upload documents
- [ ] User can chat with AI
- [ ] File downloads working
- [ ] Conversation history loading
- [ ] Analytics dashboard working
- [ ] No console errors in browser
- [ ] No errors in backend logs
- [ ] CORS working correctly
- [ ] Cookies being set correctly
- [ ] JWT tokens working correctly
- [ ] Rate limiting working
- [ ] File uploads encrypted
- [ ] Vector database accessible

## Configuration Updates

### CORS Configuration
- [ ] Backend `BACKEND_CORS_ORIGINS` updated with production frontend URL
- [ ] Backend redeployed after CORS update
- [ ] Frontend can successfully call backend API

### Domain Configuration (if using custom domains)
- [ ] Frontend custom domain configured in Vercel
- [ ] Backend custom domain configured in Render
- [ ] DNS records updated
- [ ] SSL certificates provisioned
- [ ] CORS updated to include custom domains
- [ ] Environment variables updated with custom domain URLs

## Documentation

- [ ] README updated with deployment information
- [ ] DEPLOYMENT.md created and reviewed
- [ ] Environment variable documentation updated
- [ ] API documentation updated
- [ ] Runbooks created for common operations
- [ ] Onboarding documentation updated
- [ ] Architecture diagrams updated

## Backup & Disaster Recovery

- [ ] Database backup schedule configured
- [ ] Backup retention policy defined
- [ ] Backup restoration tested
- [ ] File storage backup configured
- [ ] Vector database backup configured
- [ ] Disaster recovery plan documented
- [ ] Recovery procedures tested

## Cost & Scaling

- [ ] Cost estimates reviewed
- [ ] Budget alerts configured
- [ ] Scaling strategy defined
- [ ] Auto-scaling rules configured (if applicable)
- [ ] Resource limits reviewed
- [ ] Free tier limitations understood

## Legal & Compliance

- [ ] Terms of service created
- [ ] Privacy policy created
- [ ] Cookie consent implemented (if required)
- [ ] GDPR compliance verified (if applicable)
- [ ] Data retention policy defined
- [ ] User data deletion procedure documented

## Final Sign-Off

- [ ] Stakeholder approval obtained
- [ ] Production deployment scheduled
- [ ] Rollback plan documented
- [ ] Communication plan prepared
- [ ] Support team notified
- [ ] Monitoring team notified
- [ ] Deployment completed successfully
- [ ] Post-deployment smoke test passed
- [ ] Users notified of deployment

## Post-Deployment Tasks (within 24 hours)

- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Check database performance
- [ ] Verify backup jobs running
- [ ] Review logs for issues
- [ ] Gather user feedback
- [ ] Address any critical issues
- [ ] Document any issues found
- [ ] Update runbooks if needed

## Ongoing Maintenance

- [ ] Regular security updates
- [ ] Dependency updates
- [ ] Database maintenance
- [ ] Log review schedule
- [ ] Performance review schedule
- [ ] Cost review schedule
- [ ] Backup verification schedule
