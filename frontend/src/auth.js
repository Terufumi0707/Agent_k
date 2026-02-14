import { inject } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

export const useOptionalAuth = () => {
  // const authEnabled = inject("authEnabled", false);
  //
  // 一時的に開発環境で認証をスキップしていた処理。
  // いったんコメントアウトして通常の認証フローを利用する。
  // if (!authEnabled) {
  //   return {
  //     user: {
  //       value: {
  //         name: "ローカルユーザー"
  //       }
  //     },
  //     logout: () => {}
  //   };
  // }

  return useAuth0();
};
