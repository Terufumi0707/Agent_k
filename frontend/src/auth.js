import { inject } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

export const useOptionalAuth = () => {
  const authEnabled = inject("authEnabled", false);

  if (!authEnabled) {
    return {
      user: {
        value: {
          name: "ローカルユーザー"
        }
      },
      logout: () => {}
    };
  }

  return useAuth0();
};
