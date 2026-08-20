import { defineBackend } from '@aws-amplify/backend'
import { HttpApi, HttpMethod } from 'aws-cdk-lib/aws-apigatewayv2'
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations'
import { auth } from './auth/resource'
import { apiFunction } from './functions/api/resource'

// Amplify Data（AppSync/DynamoDB）は仕様により使わない。
// データ層は PostgreSQL + REST（SPEC.md 参照）。
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
