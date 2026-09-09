# Crusader Kings III: Legacy of Persia Mechanics (Deep Search Edition)

This document serves as an updated, comprehensive knowledge base for the `vizier-counsel` agents. It covers the advanced mechanics introduced in the *Legacy of Persia* flavor pack, which profoundly overhauled Clan governments, Middle Eastern politics, and the Iranian region.

## 1. The Iranian Intermezzo (Struggle)

The **Iranian Intermezzo** is a major "Struggle" mechanic representing the decline of the Abbasid Caliphate and the rise of independent Iranian dynasties, beginning in 867 AD.

### Struggle Phases
The struggle cycles through specific phases driven by Catalysts (player and AI actions). Each phase dramatically changes the region's rules:
*   **Unrest:** The volatile starting phase. Casus bellis are cheaper, factions are more common, and rebellion is high. Rulers are encouraged to war against different faiths/cultures.
*   **Stabilization:** A consolidation phase. Building costs are reduced, development grows faster, and internal politics/alliances take precedence over expansion.
*   **Concession:** A concluding phase reflecting shifting balances of power and compromise, often leading to a resolution of the struggle.

### Struggle Endings
The struggle can be permanently resolved via major decisions, reshaping the Middle East:
*   **Iranian Resurgence:** Replaces the Abbasid Caliph with a Persian culture ruler, breaking Arab dominance. Grants powerful dynasty modifiers.
*   **Concession / Status Quo:** Ends the struggle by formalizing the fragmented borders and rewarding dominant local rulers.
*   **Caliphate Revived:** An Arabic/Abbasid victory condition that crushes the Iranian uprising and restores centralized Caliphal authority.

### Participation & Content Additions
*   **Involvement:** Rulers are **Involved**, **Interloper**, or **Uninvolved** based on their capital location, culture, and faith.
*   **Men-at-Arms:** New localized units such as *Asawira* (Heavy Cavalry), *Tarkhan*, *Zupin* (Spearmen), and *Tawashi*.
*   **Dynasty Legacy - Brilliance:** A specific legacy tree focusing on reclaiming Persian glory, boosting education, and optimizing the new tax collection systems.

---

## 2. Clan Government & Tax Jurisdictions

The Legacy of Persia update removed standard Feudal contracts for Clan realms, replacing them with a highly dynamic **Tax Jurisdiction** system.

### Tax Collectors & Jurisdictions
*   **System:** Direct clan vassals no longer have individual contracts. Instead, they are grouped into Tax Jurisdictions (up to 12 vassals per jurisdiction).
*   **Tax Collector Role:** Each jurisdiction *must* have an assigned Tax Collector. If empty, the liege receives **0 gold and 0 levies** from those vassals.
*   **Tax Collector Aptitude:** The efficiency of extraction relies entirely on the Collector's Aptitude, calculated primarily from:
    *   **+1 per Diplomacy point** (capped at 50)
    *   **+1 per Martial point** (capped at 50)
    *   *(Note: Aptitude determines the exact percentage of taxes/levies squeezed from the vassals).*

### The Vizierate (Diarchy)
*   **Appointment:** Clan rulers (Duke-tier or higher) can spend 350 Prestige during peacetime to appoint a **Vizier**.
*   **Benefits:**
    *   Grants additional Tax Collector slots (1 to 5 extra slots, scaling with the Vizier's Stewardship).
    *   Provides a global percentage bonus to *all* Tax Collectors' aptitude based on the Vizier's own aptitude.
*   **Diarchy Mechanics:** Appointing a Vizier activates a special "Vizierate" diarchy.
    *   The Vizier gains the "Siphon Treasury" power (stealing money).
    *   The Liege gains the "Mulct Vizier" interaction to forcefully extract gold from the Vizier and shift the Scales of Power.
    *   If the Vizier is *also* serving as a Tax Collector, they receive an Aptitude bonus equal to 50% of the current Scales of Power.

---

## 3. House Unity

**House Unity** is the core stability mechanic for Clan governments, replacing standard opinion management with a house-wide cohesion system. It measures how well members of the ruling house cooperate.

### Unity Levels & Succession
Unity exists on a spectrum of 5 levels. **Critically, House Unity dictates the realm's Succession Law for Clan rulers:**
1.  **Harmonious:** The highest unity. Provides immense stability, high lifestyle experience, and acts like **High Partition** (the primary heir inherits the vast majority of titles, keeping the realm intact).
2.  **Friendly:** A stable state with moderate bonuses. Acts like standard **Partition**.
3.  **Impassive:** The neutral state.
4.  **Competitive:** Rivalries brew. Claimant factions are more likely to be accepted. Acts like **Confederate Partition** (new titles will be created to split the realm upon death).
5.  **Antagonistic:** The lowest unity. Members hate each other. Causes massive internal border wars, high faction rates, and acts like extreme **Confederate Partition**, often shattering the realm upon the ruler's death.

### Influencing Unity
*   **Increasing Unity (Toward Harmonious):** Landing family members, forming alliances with house members, and peaceful house interactions.
*   **Decreasing Unity (Toward Antagonistic):** Revoking titles from house members, imprisoning, blinding, or declaring war against relatives.
*   **House Head Decisions:** The Head of the House can take specific decisions (with a 20-year cooldown) to forcibly steer the Unity direction.

## References
- Base Game Knowledge: [[docs/CK3_STRATEGY_GUIDE.md]]
