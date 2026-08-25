import { defineBackend } from '@aws-amplify/backend'
import { HttpApi, HttpMethod } from 'aws-cdk-lib/aws-apigatewayv2'
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations'
import { auth } from './auth/resource'
import { apiFunction } from './functions/api/resource'

// Amplify Data（AppSync/DynamoDB）は使わない（docs/decisions/004 参照）。
// データ層は DynamoDB 1テーブル + REST（docs/data.md 参照）。テーブルは docs/ROADMAP.md の順序2で追加する。
const backend = defineBackend({
  auth,
  apiFunction,
})

const apiStack = backend.createStack('api-stack')

const httpApi = new HttpApi(apiStack, 'HttpApi', {
  apiName: 'rescue-pets-api',
})

httpApi.addRoutes({
  path: '/{proxy+}',
  methods: [HttpMethod.ANY],
  integration: new HttpLambdaIntegration(
    'ApiIntegration',
    backend.apiFunction.resources.lambda,
  ),
})

backend.addOutput({
  custom: {
    apiUrl: httpApi.apiEndpoint,
  },
})
