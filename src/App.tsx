import heroDog1 from './assets/hero-dog1.webp'
import heroCat from './assets/hero-cat.webp'
import heroDog2 from './assets/hero-dog2.webp'
import './App.css'

function App() {
  return (
    <main className="landing">
      <div className="photos" role="presentation">
        <img src={heroDog1} alt="" width="112" height="112" />
        <img src={heroCat} alt="" width="136" height="136" />
        <img src={heroDog2} alt="" width="112" height="112" />
      </div>
      <h1>
        rescue-pets
        <span className="subtitle">保護犬猫ポータル</span>
      </h1>
      <p className="lead">
        全国の保護犬猫の譲渡情報を、1か所で検索できるようにするWebサービスのPoCです。団体ごとに分かれている掲載を集約し、元サイトへ送客します。
      </p>
      <p className="note">掲載データはすべて架空です。実在の団体・動物の情報は使いません。</p>
      <p className="status">画面は開発中です。設計と進捗はリポジトリの README と docs/ にあります。</p>
    </main>
  )
}

export default App
