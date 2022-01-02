# digest_webhook
Webhook for Discourse Digest Email plugin

This webhook is called by a related plugin. For each call, it assembles the data into an email and sends it via SES. It runs as a service on our Lightsail instance.
