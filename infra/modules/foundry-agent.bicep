// AI Services account + project + pinned gpt-4o-mini (keyless via UAMI).
// Re-check API versions against Learn before production use.

param accountName string
param projectName string
param location string
param userPrincipalId string
param tags object = {}
param modelDeploymentName string = 'gpt-4o-mini'
param modelVersion string = '2024-07-18'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2024-10-01' = {
  parent: foundryAccount
  name: projectName
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: modelDeploymentName
  sku: { name: 'GlobalStandard', capacity: 10 }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelDeploymentName
      version: modelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}

var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
resource foundryUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, userPrincipalId, foundryUserRoleId)
  scope: foundryAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
    principalId: userPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output endpoint string = foundryAccount.properties.endpoint
output accountId string = foundryAccount.id
output accountName string = foundryAccount.name
output modelDeploymentName string = modelDeploymentName
