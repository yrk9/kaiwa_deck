import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "プライバシーポリシー | Kaiwa Deck",
};

export default function PrivacyPage() {
  return (
    <article className="mx-auto flex max-w-2xl flex-col gap-6 text-sm leading-relaxed">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">プライバシーポリシー</h1>
        <p className="text-muted-foreground">制定日: 2026年10月30日</p>
      </div>

      <p>
        Kaiwa
        Deck(以下「本サービス」)は、個人が開発・運営するWebアプリです。本サービスで取り扱う情報について、以下のとおり定めます。
      </p>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">1. 取得する情報</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            ゲストとして利用する場合: 利用者を区別するための識別子(ID)
          </li>
          <li>
            Googleアカウントでログインする場合: Googleアカウントのメールアドレスと名前
          </li>
          <li>
            利用者が作成した内容: デッキ、お題、お題を引いた記録とその日時
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">2. 利用の目的</h2>
        <p>
          取得した情報は、ログイン、作成したデッキやお題の保存など、本サービスを提供するためにのみ利用します。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">3. 第三者への提供</h2>
        <p>
          取得した情報を、第三者に販売・提供することはありません。ただし、法令に基づく場合を除きます。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">4. 外部サービスの利用</h2>
        <p>
          本サービスは、情報の保存や処理のために、次の外部サービスを利用しています。各サービスでの情報の取り扱いは、それぞれのプライバシーポリシーに従います。
        </p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Supabase(ログイン、データの保存)</li>
          <li>Google Cloud(サーバーの運用)</li>
          <li>Vercel(Webサイトの配信)</li>
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">5. ブラウザへの保存</h2>
        <p>
          ログインの状態を保つため、利用者のブラウザに情報を保存します。アクセスの解析や広告のための情報の収集は行っていません。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">6. 情報の削除</h2>
        <p>
          登録した情報の削除を希望する場合は、下記の問い合わせ先までご連絡ください。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">7. 本ポリシーの変更</h2>
        <p>
          本ポリシーの内容は、必要に応じて変更することがあります。変更した場合は、このページでお知らせします。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">8. 問い合わせ先</h2>
        <p>
          本サービスに関する問い合わせは、
          <a
            href="https://github.com/yrk9/kaiwa_deck/issues"
            className="underline underline-offset-4"
          >
            GitHubのIssues
          </a>
          までお寄せください。
        </p>
      </section>
    </article>
  );
}
