"""Fixed copy for weekly management reports."""

from netix_render.report_locale import _language

_LABELS = {
    "en": {
        "executive": "Executive summary",
        "reliability": "Reliability and comfort",
        "plant": "Plant operating patterns",
        "supporting": "Supporting measurements",
        "priorities": "Priorities for the coming week",
        "evidence": "Evidence",
        "management_implication": "Management implication",
        "next_step": "Next step · %(owner)s",
        "workload": "Where the alarm workload sits",
        "alarm_family": "Alarm family",
        "events": "Events",
        "equipment": "Equipment",
        "share": "Share",
        "daily_counts": "Daily counts of raised events. Current open alarms are shown separately above.",
        "what_changed": "What changed since last week",
        "comparison": "Alarm events: %(current)s this week, %(previous)s last week, change %(change)s.",
        "comparison_pct": "%(change)s (%(percent)s%%)",
        "zero_baseline": "The previous baseline is zero.",
        "comparison_row": "%(previous)s → %(current)s events (%(change)s).",
        "comparison_unavailable": (
            "A complete previous-period comparison is unavailable. Use a complete comparison before assessing "
            "improvement or deterioration."
        ),
        "measured_evidence": "Measured evidence",
        "operating_implication": "Operating implication",
        "required_check": "Required check · %(owner)s",
        "planning_note": (
            "Recommended work for the weekly planning meeting. Confirm assignments and dates in the work-order system."
        ),
        "priority_owner": "Priority / owner",
        "action_evidence": "Action and completion evidence",
        "proposed_due": "Proposed: %(due)s",
        "how_to_use": "How to use this report",
        "report_limits": (
            "Alarm events and their active durations measure monitoring activity. Verify failures, downtime and "
            "completed repairs against separate records. Current alarm counts reflect the collection time. "
            "Telemetry charts show measured power. An approved operating baseline is required to estimate savings."
        ),
    },
    "ar": {
        "executive": "الملخص التنفيذي",
        "reliability": "الموثوقية والراحة",
        "plant": "أنماط تشغيل المعدّات",
        "supporting": "القياسات الداعمة",
        "priorities": "أولويات الأسبوع المقبل",
        "evidence": "الأدلة",
        "management_implication": "ما يعنيه ذلك للإدارة",
        "next_step": "الخطوة التالية · %(owner)s",
        "workload": "توزيع عبء الإنذارات",
        "alarm_family": "مجموعة الإنذارات",
        "events": "الأحداث",
        "equipment": "المعدّات",
        "share": "النسبة",
        "daily_counts": "عدد مرات تفعيل الإنذارات حسب اليوم. تظهر الإنذارات المفتوحة حاليًا في قسم مستقل أعلاه.",
        "what_changed": "ما الذي تغيّر منذ الأسبوع الماضي",
        "comparison": "أحداث الإنذار: %(current)s هذا الأسبوع، و%(previous)s الأسبوع الماضي، والتغيّر %(change)s.",
        "comparison_pct": "%(change)s (%(percent)s%%)",
        "zero_baseline": "كان عدد الأحداث في فترة المقارنة صفرًا.",
        "comparison_row": "السابق: %(previous)s، الحالي: %(current)s، والتغيّر %(change)s.",
        "comparison_unavailable": "المقارنة مع الفترة السابقة غير مكتملة. يلزم اكتمالها قبل تقييم التحسّن أو التراجع.",
        "measured_evidence": "أدلة القياس",
        "operating_implication": "الأثر على التشغيل",
        "required_check": "التحقق المطلوب · %(owner)s",
        "planning_note": "الأعمال الموصى بها لاجتماع التخطيط الأسبوعي. أكّد التكليفات والمواعيد في نظام أوامر العمل.",
        "priority_owner": "الأولوية / المسؤول",
        "action_evidence": "الإجراء وإثبات الإنجاز",
        "proposed_due": "الموعد المقترح: %(due)s",
        "how_to_use": "كيفية استخدام هذا التقرير",
        "report_limits": (
            "تصف أحداث الإنذار ومدد تفعيلها نشاط المراقبة. تحقّق من الأعطال والتوقفات والإصلاحات المنجزة بالرجوع "
            "إلى سجلات منفصلة. تعكس أعداد الإنذارات الحالية لحظة جمع البيانات. تعرض مخططات القياس القدرة المقاسة. "
            "يتطلب تقدير الوفر خط أساس تشغيليًا معتمدًا."
        ),
    },
    "fr": {
        "executive": "Synthèse de direction",
        "reliability": "Fiabilité et confort",
        "plant": "Régimes de fonctionnement des équipements",
        "supporting": "Mesures à l’appui",
        "priorities": "Priorités de la semaine à venir",
        "evidence": "Éléments probants",
        "management_implication": "Implications pour la direction",
        "next_step": "Prochaine étape · %(owner)s",
        "workload": "Répartition de la charge liée aux alarmes",
        "alarm_family": "Famille d’alarmes",
        "events": "Événements",
        "equipment": "Équipements",
        "share": "Part",
        "daily_counts": (
            "Nombre de déclenchements par jour. Les alarmes actuellement ouvertes figurent séparément ci-dessus."
        ),
        "what_changed": "Évolution depuis la semaine dernière",
        "comparison": (
            "Événements d’alarme : %(current)s cette semaine, %(previous)s la semaine dernière, variation de "
            "%(change)s."
        ),
        "comparison_pct": "%(change)s (%(percent)s %%)",
        "zero_baseline": "La période de référence totalisait zéro événement.",
        "comparison_row": "%(previous)s → %(current)s événements (%(change)s).",
        "comparison_unavailable": (
            "La comparaison avec la période précédente est incomplète. Une comparaison complète est nécessaire pour "
            "évaluer une amélioration ou une dégradation."
        ),
        "measured_evidence": "Mesures à l’appui",
        "operating_implication": "Conséquences pour l’exploitation",
        "required_check": "Vérification requise · %(owner)s",
        "planning_note": (
            "Travaux recommandés pour la réunion de planification hebdomadaire. Confirmez les affectations et les "
            "dates dans le système de gestion des interventions."
        ),
        "priority_owner": "Priorité / responsable",
        "action_evidence": "Action et preuve d’achèvement",
        "proposed_due": "Échéance proposée : %(due)s",
        "how_to_use": "Comment utiliser ce rapport",
        "report_limits": (
            "Les événements d’alarme et leurs durées actives décrivent l’activité de surveillance. Vérifiez les "
            "pannes, les arrêts et les réparations effectuées dans les registres dédiés. Les totaux d’alarmes "
            "actuelles correspondent au moment de la collecte. Les graphiques de télémétrie présentent la puissance "
            "mesurée. Une référence de fonctionnement approuvée est nécessaire pour estimer les économies."
        ),
    },
    "es": {
        "executive": "Resumen ejecutivo",
        "reliability": "Fiabilidad y confort",
        "plant": "Patrones de funcionamiento de los equipos",
        "supporting": "Mediciones de respaldo",
        "priorities": "Prioridades de la próxima semana",
        "evidence": "Evidencia",
        "management_implication": "Implicaciones para la gestión",
        "next_step": "Siguiente paso · %(owner)s",
        "workload": "Distribución de la carga de alarmas",
        "alarm_family": "Familia de alarmas",
        "events": "Eventos",
        "equipment": "Equipos",
        "share": "%",
        "daily_counts": (
            "Recuento diario de activaciones. Las alarmas abiertas actualmente se muestran por separado arriba."
        ),
        "what_changed": "Cambios desde la semana pasada",
        "comparison": (
            "Eventos de alarma: %(current)s esta semana, %(previous)s la semana pasada, variación de %(change)s."
        ),
        "comparison_pct": "%(change)s (%(percent)s %%)",
        "zero_baseline": "El período de referencia anterior tuvo cero eventos.",
        "comparison_row": "%(previous)s → %(current)s eventos (%(change)s).",
        "comparison_unavailable": (
            "La comparación con el período anterior está incompleta. Se necesita una comparación completa para "
            "evaluar una mejora o un deterioro."
        ),
        "measured_evidence": "Evidencia de las mediciones",
        "operating_implication": "Implicaciones operativas",
        "required_check": "Comprobación requerida · %(owner)s",
        "planning_note": (
            "Trabajos recomendados para la reunión semanal de planificación. Confirme las asignaciones y las fechas "
            "en el sistema de órdenes de trabajo."
        ),
        "priority_owner": "Prioridad / responsable",
        "action_evidence": "Acción y evidencia de finalización",
        "proposed_due": "Plazo propuesto: %(due)s",
        "how_to_use": "Cómo usar este informe",
        "report_limits": (
            "Los eventos de alarma y su duración activa describen la actividad de supervisión. Verifique los "
            "fallos, el tiempo de inactividad y las reparaciones concluidas en registros separados. Los recuentos "
            "de alarmas actuales corresponden al momento de la recopilación. Los gráficos de telemetría muestran la "
            "potencia medida. Para estimar el ahorro se requiere una referencia operativa aprobada."
        ),
    },
    "nl": {
        "executive": "Managementsamenvatting",
        "reliability": "Betrouwbaarheid en comfort",
        "plant": "Bedrijfspatronen van installaties",
        "supporting": "Onderbouwende metingen",
        "priorities": "Prioriteiten voor komende week",
        "evidence": "Onderbouwing",
        "management_implication": "Gevolgen voor het management",
        "next_step": "Volgende stap · %(owner)s",
        "workload": "Verdeling van de alarmlast",
        "alarm_family": "Alarmgroep",
        "events": "Gebeurtenissen",
        "equipment": "Installaties",
        "share": "Aandeel",
        "daily_counts": "Aantal activeringen per dag. De huidige openstaande alarmen staan hierboven apart.",
        "what_changed": "Verandering ten opzichte van vorige week",
        "comparison": "Alarmgebeurtenissen: %(current)s deze week, %(previous)s vorige week, verschil %(change)s.",
        "comparison_pct": "%(change)s (%(percent)s%%)",
        "zero_baseline": "In de voorgaande periode waren er nul gebeurtenissen.",
        "comparison_row": "%(previous)s → %(current)s gebeurtenissen (%(change)s).",
        "comparison_unavailable": (
            "De vergelijking met de vorige periode is onvolledig. Voor een oordeel over verbetering of "
            "verslechtering is een volledige vergelijking nodig."
        ),
        "measured_evidence": "Meetgegevens",
        "operating_implication": "Gevolgen voor de bedrijfsvoering",
        "required_check": "Vereiste controle · %(owner)s",
        "planning_note": (
            "Aanbevolen werkzaamheden voor het wekelijkse planningsoverleg. Bevestig toewijzingen en datums in het "
            "werkordersysteem."
        ),
        "priority_owner": "Prioriteit / verantwoordelijke",
        "action_evidence": "Actie en bewijs van voltooiing",
        "proposed_due": "Voorgestelde datum: %(due)s",
        "how_to_use": "Hoe u dit rapport gebruikt",
        "report_limits": (
            "Alarmgebeurtenissen en hun actieve duur beschrijven de bewakingsactiviteit. Controleer storingen, "
            "stilstand en voltooide reparaties in afzonderlijke registratiegegevens. Het huidige aantal alarmen "
            "geldt op het moment van verzamelen. Telemetriegrafieken tonen het gemeten vermogen. Voor een schatting "
            "van de besparing is een goedgekeurde operationele referentie nodig."
        ),
    },
    "de": {
        "executive": "Management-Zusammenfassung",
        "reliability": "Zuverlässigkeit und Komfort",
        "plant": "Betriebsmuster der Anlagen",
        "supporting": "Ergänzende Messwerte",
        "priorities": "Prioritäten für die kommende Woche",
        "evidence": "Nachweise",
        "management_implication": "Bedeutung für das Management",
        "next_step": "Nächster Schritt · %(owner)s",
        "workload": "Verteilung der Alarmbelastung",
        "alarm_family": "Alarmgruppe",
        "events": "Ereignisse",
        "equipment": "Anlagen",
        "share": "Anteil",
        "daily_counts": "Anzahl der Auslösungen pro Tag. Aktuell offene Alarme sind oben separat aufgeführt.",
        "what_changed": "Änderung zur Vorwoche",
        "comparison": "Alarmereignisse: %(current)s diese Woche, %(previous)s in der Vorwoche, Veränderung %(change)s.",
        "comparison_pct": "%(change)s (%(percent)s %%)",
        "zero_baseline": "Im Vergleichszeitraum lag der Ausgangswert bei null.",
        "comparison_row": "%(previous)s → %(current)s Ereignisse (%(change)s).",
        "comparison_unavailable": (
            "Der Vergleich mit dem Vorzeitraum ist unvollständig. Eine Verbesserung oder Verschlechterung lässt "
            "sich erst mit einem vollständigen Vergleich beurteilen."
        ),
        "measured_evidence": "Messnachweise",
        "operating_implication": "Auswirkungen auf den Betrieb",
        "required_check": "Erforderliche Prüfung · %(owner)s",
        "planning_note": (
            "Empfohlene Arbeiten für die wöchentliche Planungssitzung. Bestätigen Sie Zuständigkeiten und Termine "
            "im Arbeitsauftragssystem."
        ),
        "priority_owner": "Priorität / Zuständigkeit",
        "action_evidence": "Maßnahme und Abschlussnachweis",
        "proposed_due": "Vorgeschlagener Termin: %(due)s",
        "how_to_use": "Hinweise zur Verwendung",
        "report_limits": (
            "Alarmereignisse und ihre aktive Dauer beschreiben die Überwachungsaktivität. Prüfen Sie Ausfälle, "
            "Stillstandszeiten und abgeschlossene Reparaturen anhand gesonderter Aufzeichnungen. Die aktuellen "
            "Alarmzahlen entsprechen dem Erfassungszeitpunkt. Telemetriediagramme zeigen die gemessene Leistung. "
            "Für die Schätzung von Einsparungen ist eine freigegebene Betriebsreferenz erforderlich."
        ),
    },
    "ru": {
        "executive": "Сводка для руководства",
        "reliability": "Надёжность и комфорт",
        "plant": "Режимы работы оборудования",
        "supporting": "Подтверждающие измерения",
        "priorities": "Приоритеты на предстоящую неделю",
        "evidence": "Подтверждающие данные",
        "management_implication": "Значение для руководства",
        "next_step": "Следующий шаг · %(owner)s",
        "workload": "Распределение нагрузки по сигналам",
        "alarm_family": "Группа сигналов",
        "events": "События",
        "equipment": "Оборуд.",
        "share": "Доля",
        "daily_counts": "Число срабатываний по дням. Открытые на момент сбора сигналы показаны отдельно выше.",
        "what_changed": "Что изменилось с прошлой недели",
        "comparison": "События: %(current)s за эту неделю, %(previous)s за прошлую, изменение %(change)s.",
        "comparison_pct": "%(change)s (%(percent)s %%)",
        "zero_baseline": "За предыдущий период событий не было.",
        "comparison_row": "События: %(previous)s → %(current)s (%(change)s).",
        "comparison_unavailable": (
            "Сравнение с предыдущим периодом неполное. Для оценки улучшения или ухудшения нужно полное сравнение."
        ),
        "measured_evidence": "Результаты измерений",
        "operating_implication": "Влияние на эксплуатацию",
        "required_check": "Необходимая проверка · %(owner)s",
        "planning_note": (
            "Рекомендуемые работы для еженедельного совещания. Подтвердите исполнителей и сроки в системе нарядов."
        ),
        "priority_owner": "Приоритет / ответственный",
        "action_evidence": "Действие и подтверждение выполнения",
        "proposed_due": "Предлагаемый срок: %(due)s",
        "how_to_use": "Как использовать отчёт",
        "report_limits": (
            "События сигнализации и продолжительность активных сигналов характеризуют работу мониторинга. "
            "Проверяйте сведения об отказах, простоях и завершённых ремонтах по отдельным журналам. Число открытых "
            "сигналов приведено на момент сбора данных. Графики телеметрии показывают измеренную мощность. Для "
            "оценки экономии нужен утверждённый базовый режим работы."
        ),
    },
}


def management_labels(locale: str) -> dict[str, str]:
    return _LABELS.get(_language(locale), _LABELS["en"])
