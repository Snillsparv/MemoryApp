# 🧠 Minnesträning - Memory Training App

En interaktiv webbapp för att träna minnet i olika discipliner.

## Funktioner

### Fyra olika minnesdiscipliner:

1. **🔢 Sifferminne**
   - Memorera sekvenser av siffror
   - Längden ökar med varje nivå
   - Börjar med 4 siffror på nivå 1

2. **📝 Ordminne**
   - Kom ihåg listor med svenska ord
   - Varierade ord från olika kategorier
   - Antal ord ökar med varje nivå

3. **🃏 Kortminne**
   - Memorera spelkort med valör och färg
   - Använder alla fyra kortfärger (♠ ♥ ♦ ♣)
   - Antal kort ökar med varje nivå

4. **🎨 Mönsterminne**
   - Kom ihåg visuella mönster i ett 5x5 rutnät
   - Klicka för att välja rätt celler under återgivning
   - Antal aktiva celler ökar med varje nivå

## Spelmekanik

- **Nivåsystem**: Varje rätt svar tar dig till nästa nivå
- **Poängsystem**: Tjäna poäng baserat på nivån (nivå × 10 poäng)
- **Highscores**: Bästa resultat sparas för varje disciplin
- **Progressiv svårighetsgrad**: Sekvenserna blir längre för varje nivå

## Hur man spelar

1. Öppna `index.html` i din webbläsare
2. Välj en minnesdisciplin
3. Memorera det som visas
4. Klicka "Jag är redo!" när du är klar
5. Återge vad du memorerat
6. Fortsätt tills du gör fel

## Teknisk information

- **Ramverk**: Vanilla JavaScript (ingen externa beroenden)
- **Lagring**: localStorage för highscores
- **Design**: Responsiv design med CSS Grid och Flexbox
- **Kompatibilitet**: Fungerar i alla moderna webbläsare

## Filstruktur

```
MemoryApp/
├── index.html      # Huvudstruktur och HTML
├── styles.css      # All styling och responsiv design
├── script.js       # Spellogik och interaktivitet
└── README.md       # Denna fil
```

## Framtida förbättringar

Möjliga förbättringar för framtiden:
- Fler discipliner (namn-ansikten, binära siffror)
- Tidsbegränsade lägen
- Multiplayer-funktionalitet
- Statistik och grafer över prestanda
- Ljudeffekter och animationer
- Olika svårighetslägen

## Licens

Fri att använda och modifiera för personligt bruk.
