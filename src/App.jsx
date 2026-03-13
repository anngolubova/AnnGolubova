import { useEffect, useMemo, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import {
  ArrowRight,
  Building2,
  ChevronRight,
  Download,
  Factory,
  FlaskConical,
  Hammer,
  Leaf,
  MapPinned,
  Menu,
  Phone,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  X,
} from 'lucide-react'

const navLinks = [
  { label: 'Продукция', href: '#catalog' },
  { label: 'О заводе', href: '#about' },
  { label: 'Лаборатория', href: '#lab' },
  { label: 'Контакты', href: '#contacts' },
]

const productCategories = [
  {
    id: 'facing',
    title: 'Облицовочный кирпич',
    subtitle: 'Классика и выразительная фактура',
    description:
      'Для фасадов, интерьерных акцентов и архитектуры, где важны точная геометрия, цветовая глубина и статусный внешний вид.',
    details: [
      'Гладкие и фактурные поверхности',
      'Натуральная палитра от песочно-бежевого до терракоты',
      'Акцент на долговечность, морозостойкость и визуальную ритмику кладки',
    ],
    icon: Sparkles,
  },
  {
    id: 'handmade',
    title: 'Кирпич ручной формовки',
    subtitle: 'Ретро-стиль и живая пластика поверхности',
    description:
      'Материал для проектов с характером: бутик-отели, премиальные резиденции и реставрационные решения с теплым винтажным ощущением.',
    details: [
      'Неоднородная фактура и благородная патина',
      'Выразительные швы и мягкая геометрия',
      'Подходит для авторской архитектуры и локальных акцентных зон',
    ],
    icon: Hammer,
  },
  {
    id: 'blocks',
    title: 'Крупноформатные керамические блоки',
    subtitle: 'Современная скорость строительства',
    description:
      'Крупноформатная керамика для энергоэффективных стеновых систем, где важны прочность, ритм монтажа и теплотехнический баланс.',
    details: [
      'Оптимизация сроков и логики монтажа',
      'Рациональная основа для малоэтажных и коммерческих объектов',
      'Материал для уверенной архитектурной геометрии',
    ],
    icon: Building2,
  },
  {
    id: 'special',
    title: 'Специализированный строительный кирпич',
    subtitle: 'Надежность для сложных задач',
    description:
      'Функциональные решения для несущих зон, специальных узлов и проектов, где критичны стабильность параметров и контроль качества.',
    details: [
      'Подбор под технические требования объекта',
      'Стабильные характеристики на каждом этапе',
      'Опора на лабораторный контроль и производственную дисциплину',
    ],
    icon: ShieldCheck,
  },
]

const trustPillars = [
  {
    title: '80+ лет истории',
    description:
      'С 1944 года завод формирует культуру работы с керамикой и сохраняет преемственность технологий.',
    icon: Factory,
  },
  {
    title: 'Собственная аккредитованная лаборатория',
    description:
      'Проверяем сырье, контролируем параметры и подтверждаем стабильность каждой производственной партии.',
    icon: FlaskConical,
  },
  {
    title: 'Экологически чистая глина',
    description:
      'Честный природный материал с выразительной текстурой и премиальным тактильным ощущением.',
    icon: Leaf,
  },
]

const masonryModes = [
  {
    name: 'Тонкий шов',
    description:
      'Акцент на ровную геометрию, чистую плоскость фасада и современную архитектурную дисциплину.',
    gap: 10,
    offset: 28,
    radius: 24,
    mortar: 'rgba(233, 221, 200, 0.38)',
    border: 'rgba(255, 255, 255, 0.08)',
    brick:
      'linear-gradient(135deg, rgba(233, 221, 200, 0.94), rgba(226, 114, 91, 0.88))',
    shadow: '0 16px 30px rgba(28, 23, 22, 0.22)',
  },
  {
    name: 'Контрастный шов',
    description:
      'Глубокий графитовый рисунок шва делает кладку более выразительной и подчеркивает премиальную фактуру кирпича.',
    gap: 14,
    offset: 36,
    radius: 28,
    mortar: 'rgba(45, 45, 45, 0.82)',
    border: 'rgba(255, 255, 255, 0.12)',
    brick:
      'linear-gradient(135deg, rgba(229, 181, 149, 0.96), rgba(221, 109, 84, 0.94))',
    shadow: '0 18px 32px rgba(12, 12, 12, 0.24)',
  },
  {
    name: 'Ручная кладка',
    description:
      'Мягкий ритм, увеличенный шов и легкая пластика кирпича создают атмосферу ремесленной архитектуры.',
    gap: 18,
    offset: 42,
    radius: 32,
    mortar: 'rgba(214, 195, 168, 0.62)',
    border: 'rgba(255, 255, 255, 0.1)',
    brick:
      'linear-gradient(135deg, rgba(197, 102, 78, 0.98), rgba(144, 70, 53, 0.92))',
    shadow: '0 20px 34px rgba(44, 28, 23, 0.28)',
  },
]

const laboratoryHighlights = [
  'Контроль физических характеристик и геометрии',
  'Проверка сырья и стабильности технологических режимов',
  'Поддержка проектировщиков и девелоперов при выборе решений',
]

function Reveal({ children, className = '', delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{
        duration: 0.8,
        delay,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      {children}
    </motion.div>
  )
}

function SectionHeading({ eyebrow, title, description }) {
  return (
    <div className="max-w-3xl">
      <p className="text-sm uppercase tracking-[0.34em] text-[#d7c2a2]">{eyebrow}</p>
      <h2 className="mt-4 text-3xl font-semibold tracking-tight text-[#f8f3ec] sm:text-4xl lg:text-5xl">
        {title}
      </h2>
      <p className="mt-5 max-w-2xl text-base leading-7 text-white/72 sm:text-lg">
        {description}
      </p>
    </div>
  )
}

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeProduct, setActiveProduct] = useState(productCategories[0].id)
  const [masonryIndex, setMasonryIndex] = useState(1)
  const [catalogUrl, setCatalogUrl] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const { scrollY } = useScroll()
  const textureY = useTransform(scrollY, [0, 700], [0, -90])
  const accentY = useTransform(scrollY, [0, 700], [0, 55])

  const currentProduct = useMemo(
    () => productCategories.find((item) => item.id === activeProduct) ?? productCategories[0],
    [activeProduct],
  )

  const currentMasonry = masonryModes[masonryIndex]

  useEffect(() => {
    const brochure = `<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <title>Каталог Голицынского керамического завода</title>
    <style>
      body { font-family: Arial, sans-serif; background:#f6f0e6; color:#2d2d2d; padding:40px; }
      .chip { display:inline-block; padding:8px 14px; border-radius:999px; background:#e2725b; color:#fff; margin-right:8px; }
      h1 { font-size:32px; margin-bottom:12px; }
      h2 { margin-top:28px; }
      .card { background:#fff; border-radius:18px; padding:24px; box-shadow:0 16px 40px rgba(45,45,45,.08); margin-top:18px; }
    </style>
  </head>
  <body>
    <span class="chip">Premium Industrial</span>
    <span class="chip" style="background:#2d2d2d;">С 1944 года</span>
    <h1>ОАО «Голицынский керамический завод»</h1>
    <p>Каталог продукции и ключевых преимуществ: облицовочный кирпич, ручная формовка, крупноформатные блоки и специализированный строительный кирпич.</p>
    <div class="card">
      <h2>Мы производим ВСЕ виды кирпича</h2>
      <ul>
        <li>Облицовочный кирпич — классика и фактура</li>
        <li>Кирпич ручной формовки — ретро-стиль</li>
        <li>Крупноформатные керамические блоки</li>
        <li>Специализированный строительный кирпич</li>
      </ul>
    </div>
    <div class="card">
      <h2>Почему нам доверяют</h2>
      <ul>
        <li>80+ лет истории производства</li>
        <li>Собственная аккредитованная лаборатория</li>
        <li>Экологически чистая глина и стабильное качество</li>
      </ul>
    </div>
  </body>
</html>`

    const url = URL.createObjectURL(
      new Blob([brochure], { type: 'text/html;charset=utf-8' }),
    )

    setCatalogUrl(url)

    return () => URL.revokeObjectURL(url)
  }, [])

  const handleFormSubmit = (event) => {
    event.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-[#1f1d1b] text-[#f8f3ec]">
      <header className="sticky top-0 z-50 px-4 pt-4">
        <div className="mx-auto max-w-7xl rounded-[30px] border border-white/10 bg-[#2d2d2d]/68 px-4 py-3 shadow-[0_18px_60px_rgba(0,0,0,0.26)] backdrop-blur-2xl sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <a href="#hero" className="flex items-center gap-3">
              <div className="grid h-12 w-12 grid-cols-2 gap-1 rounded-[18px] bg-white/6 p-2">
                <span className="rounded-[10px] bg-[#e2725b]" />
                <span className="rounded-[10px] bg-[#eadcc5]" />
                <span className="rounded-[10px] bg-[#eadcc5]" />
                <span className="rounded-[10px] bg-[#e2725b]" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-[#d7c2a2]">ОАО</p>
                <p className="text-sm font-semibold leading-5 text-white sm:text-base">
                  Голицынский керамический завод
                </p>
              </div>
            </a>

            <nav className="hidden items-center gap-8 lg:flex">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm text-white/72 transition hover:text-white"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            <div className="flex items-center gap-3">
              <a
                href={catalogUrl || '#catalog'}
                download="golitsyn-ceramic-plant-catalog.html"
                className="hidden items-center gap-2 rounded-full border border-white/12 bg-white/8 px-5 py-3 text-sm font-medium text-white transition hover:border-[#e2725b]/70 hover:bg-[#e2725b] sm:inline-flex"
              >
                <Download size={18} />
                Скачать каталог
              </a>
              <button
                type="button"
                className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-white/10 bg-white/8 text-white transition hover:bg-white/12 lg:hidden"
                onClick={() => setMenuOpen((value) => !value)}
                aria-label="Открыть меню"
              >
                {menuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </div>

        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto mt-3 max-w-7xl rounded-[28px] border border-white/10 bg-[#2d2d2d]/88 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.32)] backdrop-blur-xl lg:hidden"
          >
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="rounded-[22px] px-4 py-3 text-sm text-white/80 transition hover:bg-white/8 hover:text-white"
                  onClick={() => setMenuOpen(false)}
                >
                  {link.label}
                </a>
              ))}
              <a
                href={catalogUrl || '#catalog'}
                download="golitsyn-ceramic-plant-catalog.html"
                className="mt-2 inline-flex items-center justify-center gap-2 rounded-[22px] bg-[#e2725b] px-4 py-3 text-sm font-medium text-white shadow-[0_18px_36px_rgba(226,114,91,0.28)]"
              >
                <Download size={18} />
                Скачать каталог
              </a>
            </div>
          </motion.div>
        )}
      </header>

      <main className="px-4 pb-10 pt-4 sm:pb-16">
        <section
          id="hero"
          className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[1.15fr_0.85fr]"
        >
          <motion.div
            className="relative overflow-hidden rounded-[40px] border border-white/10 bg-[linear-gradient(135deg,rgba(226,114,91,0.18),rgba(33,31,30,0.88)_48%,rgba(233,221,200,0.18))] p-6 shadow-[0_26px_120px_rgba(0,0,0,0.28)] sm:p-10"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div
              className="brick-texture absolute inset-0 opacity-60"
              style={{ y: textureY }}
            />
            <motion.div
              className="absolute -right-16 top-12 h-56 w-56 rounded-full bg-[#e2725b]/24 blur-3xl"
              style={{ y: accentY }}
            />
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#e8c39e]/20 bg-white/8 px-4 py-2 text-xs uppercase tracking-[0.3em] text-[#e8c39e]">
                <Factory size={16} />
                Premium Industrial
              </div>

              <h1 className="mt-8 max-w-4xl text-4xl font-semibold leading-[1.02] tracking-tight text-white sm:text-5xl lg:text-7xl">
                Искусство керамического совершенства с 1944 года
              </h1>

              <p className="mt-6 max-w-2xl text-base leading-7 text-white/74 sm:text-lg">
                Голицынский керамический завод создает материалы для архитектуры, которая
                выглядит статусно, работает десятилетиями и передает ощущение надежности уже
                с первого взгляда на фасад.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  href="#catalog"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[#e2725b] px-6 py-3.5 text-sm font-medium text-white shadow-[0_18px_34px_rgba(226,114,91,0.28)] transition hover:translate-y-[-1px] hover:bg-[#ef826d]"
                >
                  Смотреть продукцию
                  <ArrowRight size={18} />
                </a>
                <a
                  href="#contacts"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-white/12 bg-white/6 px-6 py-3.5 text-sm font-medium text-white transition hover:border-white/24 hover:bg-white/10"
                >
                  Запросить консультацию
                  <ChevronRight size={18} />
                </a>
              </div>

              <div className="mt-10 grid gap-4 sm:grid-cols-3">
                {trustPillars.map((item, index) => {
                  const Icon = item.icon

                  return (
                    <Reveal
                      key={item.title}
                      delay={0.1 + index * 0.08}
                      className="rounded-[30px] border border-white/10 bg-white/6 p-5 backdrop-blur-xl"
                    >
                      <Icon size={22} className="text-[#e8c39e]" />
                      <h2 className="mt-4 text-lg font-semibold text-white">{item.title}</h2>
                      <p className="mt-2 text-sm leading-6 text-white/68">{item.description}</p>
                    </Reveal>
                  )
                })}
              </div>
            </div>
          </motion.div>

          <div className="grid gap-6">
            <Reveal className="rounded-[36px] border border-white/10 bg-[#262321] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.22)] sm:p-8">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-[#d7c2a2]">
                    Фирменная палитра
                  </p>
                  <p className="mt-2 text-lg font-semibold text-white">
                    Терракота, глубокий графит и песочно-бежевые нюансы
                  </p>
                </div>
                <div className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs uppercase tracking-[0.22em] text-white/60">
                  brick grid
                </div>
              </div>

              <div className="mt-7 grid gap-3 sm:grid-cols-3">
                {[
                  ['Терракотовый', '#E2725B'],
                  ['Глубокий графит', '#2D2D2D'],
                  ['Песочно-бежевый', '#E9DDC8'],
                ].map(([label, color]) => (
                  <div
                    key={label}
                    className="rounded-[28px] border border-white/8 bg-white/4 p-4"
                  >
                    <div
                      className="h-24 rounded-[24px]"
                      style={{
                        background: `linear-gradient(160deg, ${color}, rgba(255,255,255,0.7))`,
                      }}
                    />
                    <p className="mt-4 text-sm font-medium text-white">{label}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.22em] text-white/42">
                      {color}
                    </p>
                  </div>
                ))}
              </div>
            </Reveal>

            <Reveal
              delay={0.12}
              className="relative overflow-hidden rounded-[36px] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)] sm:p-8"
            >
              <div className="absolute inset-0 brick-grid opacity-50" />
              <div className="relative">
                <div className="flex items-center gap-2 text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">
                  <ShieldCheck size={17} />
                  Надежность материала
                </div>
                <p className="mt-4 max-w-md text-2xl font-semibold leading-tight text-white">
                  Материал, который ощущается монументально и выглядит премиально.
                </p>
                <p className="mt-3 max-w-md text-sm leading-6 text-white/66">
                  Мы проектируем визуальную уверенность: крупные радиусы, плотные блоки и
                  текстуру кладки, отсылающую к реальному кирпичу премиального формования.
                </p>

                <div className="mt-8 space-y-3">
                  {[0, 1, 2, 3].map((row) => (
                    <div
                      key={row}
                      className="flex"
                      style={{
                        gap: '12px',
                        transform: `translateX(${row % 2 === 0 ? 0 : 28}px)`,
                      }}
                    >
                      {Array.from({ length: row % 2 === 0 ? 5 : 4 }).map((_, brickIndex) => (
                        <div
                          key={`${row}-${brickIndex}`}
                          className="min-h-[64px] flex-1 rounded-[24px] border border-white/10"
                          style={{
                            background:
                              brickIndex % 2 === 0
                                ? 'linear-gradient(160deg, rgba(237,188,160,0.95), rgba(226,114,91,0.88))'
                                : 'linear-gradient(160deg, rgba(233,221,200,0.94), rgba(214,154,124,0.88))',
                          }}
                        />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>
        </section>

        <section id="catalog" className="mx-auto mt-8 max-w-7xl">
          <Reveal className="rounded-[40px] border border-white/10 bg-[#24211f] p-6 shadow-[0_24px_100px_rgba(0,0,0,0.2)] sm:p-10">
            <SectionHeading
              eyebrow="Каталог"
              title="Мы производим ВСЕ виды кирпича"
              description="Каталог построен как премиальная система материалов: от точной облицовки до крупных керамических блоков и специализированных решений для строительных задач."
            />

            <div className="mt-10 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="grid gap-4">
                {productCategories.map((item, index) => {
                  const Icon = item.icon
                  const isActive = currentProduct.id === item.id

                  return (
                    <motion.button
                      key={item.id}
                      type="button"
                      className={`group rounded-[30px] border p-5 text-left transition ${
                        isActive
                          ? 'border-[#e2725b]/70 bg-[#e2725b]/10 shadow-[0_22px_50px_rgba(226,114,91,0.14)]'
                          : 'border-white/8 bg-white/[0.04] hover:border-white/16 hover:bg-white/[0.06]'
                      }`}
                      onClick={() => setActiveProduct(item.id)}
                      whileHover={{ y: -4 }}
                      initial={{ opacity: 0, y: 24 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true, amount: 0.2 }}
                      transition={{ duration: 0.55, delay: index * 0.08 }}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="rounded-[22px] border border-white/10 bg-white/8 p-3">
                          <Icon size={22} className="text-[#e8c39e]" />
                        </div>
                        <div className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/8 text-white/70 transition group-hover:text-white">
                          <ArrowRight size={18} />
                        </div>
                      </div>
                      <h3 className="mt-5 text-xl font-semibold text-white">{item.title}</h3>
                      <p className="mt-2 text-sm uppercase tracking-[0.22em] text-[#d7c2a2]">
                        {item.subtitle}
                      </p>
                      <p className="mt-4 text-sm leading-6 text-white/66">{item.description}</p>
                    </motion.button>
                  )
                })}
              </div>

              <Reveal delay={0.12} className="rounded-[34px] border border-white/10 bg-white/[0.04] p-6 sm:p-8">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full border border-[#e2725b]/30 bg-[#e2725b]/12 px-4 py-2 text-xs uppercase tracking-[0.24em] text-[#ffc9bd]">
                    Выбранная категория
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs uppercase tracking-[0.24em] text-white/56">
                    Premium Industrial UI
                  </span>
                </div>

                <h3 className="mt-6 text-3xl font-semibold leading-tight text-white sm:text-4xl">
                  {currentProduct.title}
                </h3>
                <p className="mt-3 text-base leading-7 text-white/72">
                  {currentProduct.description}
                </p>

                <div className="mt-8 grid gap-4 sm:grid-cols-3">
                  {currentProduct.details.map((detail) => (
                    <div
                      key={detail}
                      className="rounded-[26px] border border-white/8 bg-[#1f1d1b] p-4"
                    >
                      <p className="text-sm leading-6 text-white/74">{detail}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-8 rounded-[30px] border border-white/10 bg-[#1b1a18] p-5">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">
                        Архитектурный эффект
                      </p>
                      <p className="mt-3 max-w-xl text-lg leading-8 text-white/76">
                        Каждая категория проектируется так, чтобы кладка читалась глубоко,
                        массивно и тактильно: через шов, оттенок, радиус и светотень.
                      </p>
                    </div>
                    <a
                      href="#contacts"
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-5 py-3 text-sm font-medium text-white transition hover:bg-[#e2725b] hover:border-[#e2725b]"
                    >
                      Подобрать решение
                      <ChevronRight size={18} />
                    </a>
                  </div>
                </div>
              </Reveal>
            </div>

            <Reveal delay={0.16} className="mt-8 rounded-[34px] border border-white/10 bg-[#1d1b19] p-6 sm:p-8">
              <div className="grid gap-8 xl:grid-cols-[0.76fr_1.24fr]">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs uppercase tracking-[0.26em] text-[#d7c2a2]">
                    <SlidersHorizontal size={16} />
                    Демонстрация кладки
                  </div>
                  <h3 className="mt-6 text-3xl font-semibold text-white sm:text-4xl">
                    Переключатель текстур и швов
                  </h3>
                  <p className="mt-4 max-w-xl text-base leading-7 text-white/72">
                    Меняйте характер фасада: тонкий аккуратный шов для современной архитектуры,
                    контрастный ритм для статусных объемов или ремесленную пластику ручной
                    формовки.
                  </p>

                  <div className="mt-8 rounded-[28px] border border-white/10 bg-white/[0.04] p-5">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-lg font-semibold text-white">{currentMasonry.name}</p>
                        <p className="mt-2 text-sm leading-6 text-white/66">
                          {currentMasonry.description}
                        </p>
                      </div>
                      <span className="rounded-full border border-white/10 bg-white/8 px-4 py-2 text-xs uppercase tracking-[0.24em] text-white/56">
                        {masonryIndex + 1} / {masonryModes.length}
                      </span>
                    </div>

                    <input
                      type="range"
                      min="0"
                      max={masonryModes.length - 1}
                      step="1"
                      value={masonryIndex}
                      onChange={(event) => setMasonryIndex(Number(event.target.value))}
                      className="mortar-slider mt-6 w-full"
                      aria-label="Переключение режима кладки"
                    />

                    <div className="mt-4 flex flex-wrap gap-2">
                      {masonryModes.map((mode, index) => (
                        <button
                          key={mode.name}
                          type="button"
                          className={`rounded-full border px-4 py-2 text-xs uppercase tracking-[0.22em] transition ${
                            masonryIndex === index
                              ? 'border-[#e2725b]/70 bg-[#e2725b]/14 text-[#ffc7bb]'
                              : 'border-white/10 bg-white/6 text-white/56 hover:text-white'
                          }`}
                          onClick={() => setMasonryIndex(index)}
                        >
                          {mode.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div
                  className="rounded-[34px] border border-white/10 p-4 sm:p-6"
                  style={{ backgroundColor: currentMasonry.mortar }}
                >
                  <div className="space-y-4 overflow-hidden rounded-[28px] bg-[#151413]/22 p-4 sm:p-6">
                    {Array.from({ length: 5 }).map((_, rowIndex) => (
                      <div
                        key={rowIndex}
                        className="flex"
                        style={{
                          gap: `${currentMasonry.gap}px`,
                          transform: `translateX(${rowIndex % 2 === 0 ? 0 : currentMasonry.offset}px)`,
                        }}
                      >
                        {Array.from({ length: rowIndex % 2 === 0 ? 5 : 4 }).map((_, brickIndex) => (
                          <motion.div
                            key={`${rowIndex}-${brickIndex}`}
                            className="flex-1 border"
                            style={{
                              minHeight: brickIndex % 3 === 0 ? '84px' : '70px',
                              borderRadius: `${currentMasonry.radius}px`,
                              borderColor: currentMasonry.border,
                              background: currentMasonry.brick,
                              boxShadow: currentMasonry.shadow,
                            }}
                            initial={{ opacity: 0, y: 16 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, amount: 0.2 }}
                            transition={{
                              duration: 0.45,
                              delay: rowIndex * 0.08 + brickIndex * 0.03,
                            }}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Reveal>
          </Reveal>
        </section>

        <section id="about" className="mx-auto mt-8 max-w-7xl">
          <Reveal className="rounded-[40px] border border-white/10 bg-[#262321] p-6 shadow-[0_24px_100px_rgba(0,0,0,0.2)] sm:p-10">
            <SectionHeading
              eyebrow="Доверие"
              title="Нас выбирают за стабильность материала, производства и сервиса"
              description="Премиальный образ бренда строится не только на эстетике, но и на инженерной дисциплине: история, лаборатория и природное сырье работают как единая система доверия."
            />

            <div className="mt-10 grid gap-5 lg:grid-cols-3">
              {trustPillars.map((item, index) => {
                const Icon = item.icon

                return (
                  <Reveal
                    key={item.title}
                    delay={0.08 * index}
                    className="rounded-[32px] border border-white/10 bg-white/[0.04] p-6"
                  >
                    <div className="flex h-14 w-14 items-center justify-center rounded-[22px] border border-white/10 bg-white/8">
                      <Icon size={24} className="text-[#e8c39e]" />
                    </div>
                    <h3 className="mt-5 text-2xl font-semibold text-white">{item.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-white/68">{item.description}</p>
                  </Reveal>
                )
              })}
            </div>

            <div className="mt-8 grid gap-5 lg:grid-cols-[1.12fr_0.88fr]">
              <Reveal className="rounded-[34px] border border-white/10 bg-[linear-gradient(145deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-6 sm:p-8">
                <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">Философия бренда</p>
                <p className="mt-5 max-w-2xl text-2xl font-semibold leading-tight text-white sm:text-3xl">
                  Плотный визуальный язык, честный материал и архитектурный ритм кирпичной
                  кладки.
                </p>
                <p className="mt-4 max-w-2xl text-base leading-7 text-white/70">
                  Сетка секций вдохновлена кирпичной раскладкой, крупные радиусы повторяют
                  форму премиального формованного кирпича, а стеклянные слои навигации и
                  карточек подчеркивают современный подход завода.
                </p>
              </Reveal>

              <Reveal delay={0.1} className="brick-grid rounded-[34px] border border-white/10 p-6 sm:p-8">
                <div className="rounded-[28px] border border-white/10 bg-[#1b1a18]/88 p-6 backdrop-blur-sm">
                  <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">Контроль качества</p>
                  <div className="mt-5 space-y-4">
                    {[
                      'Стабильный визуальный тон партии',
                      'Технологическая дисциплина производства',
                      'Материал для частного и коммерческого строительства',
                    ].map((point) => (
                      <div
                        key={point}
                        className="flex items-start gap-3 rounded-[22px] border border-white/8 bg-white/[0.04] p-4"
                      >
                        <ShieldCheck size={20} className="mt-0.5 text-[#e8c39e]" />
                        <p className="text-sm leading-6 text-white/72">{point}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Reveal>
            </div>
          </Reveal>
        </section>

        <section id="lab" className="mx-auto mt-8 max-w-7xl">
          <Reveal className="rounded-[40px] border border-white/10 bg-[#1f1d1b] p-6 shadow-[0_24px_100px_rgba(0,0,0,0.2)] sm:p-10">
            <SectionHeading
              eyebrow="Лаборатория"
              title="Собственная лаборатория как часть инженерной репутации завода"
              description="Лабораторный блок усиливает доверие к бренду: помогает подтверждать свойства материалов, поддерживать стабильность и сопровождать выбор архитектурных решений."
            />

            <div className="mt-10 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
              <Reveal className="rounded-[34px] border border-white/10 bg-white/[0.04] p-6 sm:p-8">
                <div className="flex items-center gap-3">
                  <div className="rounded-[22px] border border-white/10 bg-white/8 p-3">
                    <FlaskConical size={24} className="text-[#e8c39e]" />
                  </div>
                  <div>
                    <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">
                      Аккредитованная экспертиза
                    </p>
                    <p className="mt-1 text-xl font-semibold text-white">
                      Лаборатория сопровождает каждую производственную серию
                    </p>
                  </div>
                </div>

                <div className="mt-8 space-y-4">
                  {laboratoryHighlights.map((item) => (
                    <div
                      key={item}
                      className="rounded-[24px] border border-white/8 bg-[#181715] p-4"
                    >
                      <p className="text-sm leading-6 text-white/72">{item}</p>
                    </div>
                  ))}
                </div>
              </Reveal>

              <Reveal delay={0.1} className="grid gap-5 sm:grid-cols-2">
                <div className="rounded-[32px] border border-white/10 bg-[linear-gradient(160deg,rgba(226,114,91,0.16),rgba(255,255,255,0.03))] p-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">1944</p>
                  <p className="mt-4 text-3xl font-semibold text-white">Старт истории</p>
                  <p className="mt-3 text-sm leading-6 text-white/68">
                    С этого момента завод последовательно развивает культуру производства
                    керамики и сохраняет ремесленную ценность материала.
                  </p>
                </div>
                <div className="rounded-[32px] border border-white/10 bg-white/[0.04] p-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">Сегодня</p>
                  <p className="mt-4 text-3xl font-semibold text-white">Современный язык бренда</p>
                  <p className="mt-3 text-sm leading-6 text-white/68">
                    Завод соединяет индустриальную надежность, экологичное сырье и визуальную
                    выразительность премиальной кладки.
                  </p>
                </div>
                <div className="sm:col-span-2 rounded-[34px] border border-white/10 bg-[#262321] p-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">
                    Для проектировщиков и девелоперов
                  </p>
                  <p className="mt-4 max-w-3xl text-lg leading-8 text-white/74">
                    Лабораторный контур делает коммуникацию с материалом профессиональной:
                    проще согласовывать фактуры, оценивать сценарии применения и формировать
                    доверие к продукту на ранней стадии проекта.
                  </p>
                </div>
              </Reveal>
            </div>
          </Reveal>
        </section>

        <footer id="contacts" className="mx-auto mt-8 max-w-7xl">
          <Reveal className="rounded-[40px] border border-white/10 bg-[#24211f] p-6 shadow-[0_24px_100px_rgba(0,0,0,0.22)] sm:p-10">
            <div className="grid gap-6 xl:grid-cols-[1fr_0.92fr]">
              <div className="overflow-hidden rounded-[34px] border border-white/10 bg-white/[0.04]">
                <div className="border-b border-white/10 p-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">Контакты и карта</p>
                  <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
                    Производство, логистика и консультации в одном контуре
                  </h2>
                  <p className="mt-3 max-w-2xl text-base leading-7 text-white/70">
                    Оставьте заявку на подбор материала, фактур и технической консультации.
                    Карта встроена в блок, чтобы пользователь сразу видел географию завода.
                  </p>
                </div>

                <div className="grid gap-5 p-6">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-[26px] border border-white/8 bg-[#1b1a18] p-4">
                      <div className="flex items-center gap-3">
                        <MapPinned size={20} className="text-[#e8c39e]" />
                        <p className="text-sm font-medium text-white">Московская область</p>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-white/68">
                        г. Голицыно, промышленный кластер завода и логистической отгрузки.
                      </p>
                    </div>

                    <div className="rounded-[26px] border border-white/8 bg-[#1b1a18] p-4">
                      <div className="flex items-center gap-3">
                        <Phone size={20} className="text-[#e8c39e]" />
                        <p className="text-sm font-medium text-white">Коммерческий отдел</p>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-white/68">
                        +7 (495) 555-24-44
                        <br />
                        sales@golitsyn-ceramic.ru
                      </p>
                    </div>
                  </div>

                  <div className="overflow-hidden rounded-[30px] border border-white/10">
                    <iframe
                      title="Карта Голицынского керамического завода"
                      src="https://www.openstreetmap.org/export/embed.html?bbox=36.959%2C55.606%2C37.036%2C55.661&layer=mapnik&marker=55.635%2C36.995"
                      className="h-[320px] w-full"
                      loading="lazy"
                    />
                  </div>
                </div>
              </div>

              <div className="rounded-[34px] border border-white/10 bg-[linear-gradient(160deg,rgba(226,114,91,0.14),rgba(255,255,255,0.04))] p-6 sm:p-8">
                <p className="text-sm uppercase tracking-[0.28em] text-[#d7c2a2]">Форма захвата лидов</p>
                <h3 className="mt-4 text-3xl font-semibold text-white">Получить каталог и консультацию</h3>
                <p className="mt-3 text-base leading-7 text-white/72">
                  Заполните форму — и мы свяжемся с вами, чтобы подобрать линейку продукции,
                  варианты фактур и формат поставки под ваш проект.
                </p>

                <form className="mt-8 space-y-4" onSubmit={handleFormSubmit}>
                  <label className="block">
                    <span className="mb-2 block text-sm text-white/62">Ваше имя</span>
                    <input
                      type="text"
                      required
                      placeholder="Например, Анна"
                      className="form-input"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm text-white/62">Телефон или email</span>
                    <input
                      type="text"
                      required
                      placeholder="+7 (___) ___-__-__"
                      className="form-input"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm text-white/62">Кратко о проекте</span>
                    <textarea
                      required
                      rows="4"
                      placeholder="Фасад частного дома, общественный объект, реставрация или коммерческая застройка"
                      className="form-input min-h-[132px] resize-none"
                    />
                  </label>

                  <button
                    type="submit"
                    className="inline-flex w-full items-center justify-center gap-2 rounded-[26px] border border-[#f4af9f]/20 bg-[#e2725b] px-6 py-4 text-sm font-semibold text-white shadow-[0_22px_44px_rgba(226,114,91,0.3)] transition hover:translate-y-[-1px] hover:bg-[#ef826d]"
                  >
                    Получить предложение
                    <ArrowRight size={18} />
                  </button>
                </form>

                <div className="mt-6 rounded-[26px] border border-white/10 bg-[#1c1a18] p-4 text-sm leading-6 text-white/70">
                  {submitted ? (
                    <p>
                      Спасибо! Заявка выглядит как качественный лид: менеджер может связаться
                      для подбора линейки кирпича, формата шва и каталога.
                    </p>
                  ) : (
                    <p>
                      Кнопка выполнена в «кирпичном» стиле: крупная, массивная и тактильно
                      заметная, чтобы завершать премиальный пользовательский сценарий.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-8 flex flex-col gap-4 border-t border-white/10 pt-6 text-sm text-white/48 sm:flex-row sm:items-center sm:justify-between">
              <p>ОАО «Голицынский керамический завод» — premium industrial landing concept.</p>
              <div className="flex flex-wrap gap-3">
                <a href="#hero" className="transition hover:text-white">
                  Наверх
                </a>
                <a href={catalogUrl || '#catalog'} download="golitsyn-ceramic-plant-catalog.html" className="transition hover:text-white">
                  Скачать каталог
                </a>
              </div>
            </div>
          </Reveal>
        </footer>
      </main>
    </div>
  )
}
