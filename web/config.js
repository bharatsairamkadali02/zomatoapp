/**
 * TIER 1 — Web Server Configuration
 * -----------------------------------
 * Set API_BASE to the PUBLIC IP or domain of your Tier 2 App Server EC2 instance.
 * Example: const API_BASE = 'http://13.235.100.200:5000';
 *
 * Leave APP_SERVER_IP as-is; replace it with your actual App Server IP after deployment.
 */
const API_BASE = 'http://APP_SERVER_IP:5000';
