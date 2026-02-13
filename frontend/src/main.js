import { createApp } from "vue";
import { createAuth0 } from "@auth0/auth0-vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";

const app = createApp(App);

const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
const hasAuth0Config =
  Boolean(auth0Domain) &&
  Boolean(auth0ClientId) &&
  auth0Domain !== "your-tenant.us.auth0.com" &&
  auth0ClientId !== "your-client-id";

app.provide("authEnabled", hasAuth0Config);

if (hasAuth0Config) {
  app.use(
    createAuth0({
      domain: auth0Domain,
      clientId: auth0ClientId,
      authorizationParams: {
        redirect_uri:
          import.meta.env.VITE_AUTH0_REDIRECT_URI || window.location.origin,
        scope: "openid profile email"
      },
      cacheLocation: "memory",
      useRefreshTokens: true
    })
  );
} else {
  console.warn(
    "Auth0 settings are missing. Running frontend without authentication guard."
  );
}

app.use(router);
app.mount("#app");
