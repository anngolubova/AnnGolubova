const productionStages = [
  {
    title: 'Подготовка сырья',
    text: 'Отбор и подготовка глины, контроль влажности и состава для стабильной прочности будущего кирпича.',
  },
  {
    title: 'Формование',
    text: 'Точное формование заготовок с соблюдением геометрии для качественной кладки и аккуратного шва.',
  },
  {
    title: 'Сушка и обжиг',
    text: 'Многоэтапная сушка и обжиг в печах для достижения высокой морозостойкости и долговечности.',
  },
  {
    title: 'Контроль качества',
    text: 'Проверка каждой партии по основным характеристикам и подготовка к упаковке и отгрузке.',
  },
]

const brickTypes = [
  'Облицовочный кирпич',
  'Рядовой строительный кирпич',
  'Полнотелый кирпич',
  'Пустотелый кирпич',
  'Клинкерный кирпич',
  'Шамотный (огнеупорный) кирпич',
  'Кирпич ручной формовки',
  'Крупноформатные керамические блоки',
]

const advantages = [
  'Современное производство и контроль на каждом этапе',
  'Стабильная геометрия и надежные эксплуатационные свойства',
  'Решения для частного, коммерческого и промышленного строительства',
]

export default function App() {
  return (
    <div className="page">
      <header className="hero" id="top">
        <div className="container">
          <div className="hero-badge">ОАО «Голицынский керамический завод»</div>
          <h1>Производство кирпича полного цикла</h1>
          <p className="hero-text">
            Надежный российский производитель керамических материалов с акцентом на качество,
            долговечность и стабильную геометрию продукции.
          </p>
          <a className="hero-button" href="#types">
            Смотреть ассортимент
          </a>
        </div>
      </header>

      <main className="container">
        <section className="section" id="production">
          <h2>Блоки производственного процесса</h2>
          <p className="section-intro">
            Производство кирпича организовано по этапам, где каждый блок отвечает за качество
            конечного продукта.
          </p>

          <div className="grid stages-grid">
            {productionStages.map((stage) => (
              <article className="card brick-card" key={stage.title}>
                <h3>{stage.title}</h3>
                <p>{stage.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="types">
          <h2>Ассортимент продукции</h2>
          <p className="highlight">
            Важно: ОАО «Голицынский керамический завод» производит <strong>все виды кирпича</strong>.
          </p>

          <div className="grid types-grid">
            {brickTypes.map((type) => (
              <div className="type-tile" key={type}>
                {type}
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <h2>Почему выбирают завод</h2>
          <div className="grid advantages-grid">
            {advantages.map((item) => (
              <div className="card" key={item}>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer" id="contacts">
        <div className="container footer-inner">
          <div>
            <h2>Контакты</h2>
            <p>Отдел продаж: +7 (495) 555-24-44</p>
            <p>Email: sales@gkz-brick.ru</p>
          </div>
          <a className="hero-button" href="#top">
            Наверх
          </a>
        </div>
      </footer>
    </div>
  )
}
