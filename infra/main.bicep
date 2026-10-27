// Coach Training Desk — subscription-scoped stack for azd up.
// Identity + Log Analytics + ACR + ACA. Foundry is optional (see deployFoundry).

targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('azd environment name (e.g. coachdesk)')
param environmentName string

@minLength(1)
@description('Primary Azure region')
param location string = 'westus2'

@description('Developer principal ID for optional local RBAC (unused in CI)')
param principalId string = ''

@description('Provision Azure AI Foundry + model (requires OpenAI access on the subscription)')
param deployFoundry bool = false

var resourceGroupName = 'rg-${environmentName}'
var identityName = 'id-${environmentName}'
var logAnalyticsName = 'log-${environmentName}'
var containerAppsEnvName = 'cae-${environmentName}'
var containerAppName = 'ca-api-${environmentName}'
var foundryAccountName = 'aif${replace(environmentName, '-', '')}${take(uniqueString(subscription().id), 6)}'
var foundryProjectName = 'proj-coachdesk'
var acrName = 'acr${replace(environmentName, '-', '')}${take(uniqueString(subscription().id), 6)}'

var tags = {
  'azd-env-name': environmentName
  hackathon: 'inside-the-game'
  project: 'coach-training-desk'
}

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    identityName: identityName
    location: location
    tags: tags
  }
}

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  scope: rg
  params: {
    workspaceName: logAnalyticsName
    location: location
    tags: tags
  }
}

module containerAppsEnv 'modules/container-app-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    envName: containerAppsEnvName
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    tags: tags
  }
}

module acr 'modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    registryName: acrName
    location: location
    userIdentityId: identity.outputs.identityId
    tags: tags
  }
}

module foundry 'modules/foundry-agent.bicep' = if (deployFoundry) {
  name: 'foundry'
  scope: rg
  params: {
    accountName: foundryAccountName
    projectName: foundryProjectName
    location: location
    userPrincipalId: identity.outputs.principalId
    tags: tags
  }
}

var foundryEnvVars = deployFoundry ? [
  { name: 'AZURE_AI_PROJECT_ENDPOINT', value: foundry.?outputs.?endpoint ?? '' }
  { name: 'AZURE_AI_MODEL_DEPLOYMENT', value: foundry.?outputs.?modelDeploymentName ?? 'gpt-4o-mini' }
] : []

module containerApp 'modules/container-app.bicep' = {
  name: 'container-app'
  scope: rg
  params: {
    appName: containerAppName
    containerAppsEnvId: containerAppsEnv.outputs.envId
    userIdentityId: identity.outputs.identityId
    userIdentityClientId: identity.outputs.clientId
    // Placeholder — azd deploy overwrites via azd-service-name tag.
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest'
    location: location
    registryServer: acr.outputs.loginServer
    tags: union(tags, { 'azd-service-name': 'api' })
    envVars: concat(
      [
        { name: 'DEFAULT_PERSONA', value: 'coach' }
      ],
      foundryEnvVars
    )
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_APP_NAME string = containerAppName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer
output AZURE_ACR_LOGIN_SERVER string = acr.outputs.loginServer
output AZURE_MANAGED_IDENTITY_CLIENT_ID string = identity.outputs.clientId
output FOUNDRY_PROJECT_ENDPOINT string = foundry.?outputs.?endpoint ?? ''
output APP_URL string = containerApp.outputs.appUrl

