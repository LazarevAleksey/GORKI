# init_constructor_data.py
import sqlite3
import json

DB_PATH = "retarders_complete.db"

def init_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, есть ли данные в section_types
    cursor.execute("SELECT COUNT(*) FROM section_types")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO section_types (name, code) VALUES (?, ?)", [
            ('надвижная часть', 'надвиг'),
            ('спускная часть', 'спуск'),
            ('парковая часть', 'парк')
        ])
        print("✅ Добавлены section_types")
    
    # Проверяем, есть ли данные в zone_types
    cursor.execute("SELECT COUNT(*) FROM zone_types")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO zone_types (name, code) VALUES (?, ?)", [
            ('головная зона', 'голова'),
            ('пучковая зона', 'пучок')
        ])
        print("✅ Добавлены zone_types")
    
    # Создаём тестовый шаблон для СПСМ горка № 3
    cursor.execute("SELECT COUNT(*) FROM park_templates")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO park_templates (name, description, is_default)
            VALUES (?, ?, ?)
        """, ("Типовая горка СПСМ", "Шаблон для СПСМ горка № 3 и № 4", 1))
        template_id = cursor.lastrowid
        
        # Элементы шаблона
        elements = [
            # Надвижная часть
            (template_id, 'section', None, 1, None, 'Путь надвига 1', 'НП-1', 1, json.dumps({"length_m": 200, "has_track_circuit": True})),
            (template_id, 'section', None, 1, None, 'Путь надвига 2', 'НП-2', 2, json.dumps({"length_m": 150, "has_track_circuit": True})),
            (template_id, 'section', None, 1, None, 'Стрелочный участок 1', 'НП-С1', 10, json.dumps({"is_switch_section": True})),
            (template_id, 'section', None, 1, None, 'Стрелочный участок 2', 'НП-С2', 11, json.dumps({"is_switch_section": True})),
            
            # Спускная часть - головная зона
            (template_id, 'section', None, 2, 1, 'Скоростной участок', 'ГЗ-СУ', 1, json.dumps({"length_m": 120})),
            (template_id, 'section', None, 2, 1, 'Измерительный участок', 'ГЗ-ИУ', 2, json.dumps({"is_measuring_section": True, "length_m": 80})),
            (template_id, 'section', None, 2, 1, 'Стрелочная зона', 'ГЗ-СЗ', 3, json.dumps({"is_switch_section": True})),
            (template_id, 'section', None, 2, 1, '1 тормозная позиция', 'ГЗ-1ТП', 4, json.dumps({})),
            
            # Спускная часть - пучковая зона
            (template_id, 'section', None, 2, 2, 'Бесстрелочный участок', 'ПЗ-БУ', 1, json.dumps({"length_m": 100})),
            (template_id, 'section', None, 2, 2, 'Стрелочная зона', 'ПЗ-СЗ', 2, json.dumps({"is_switch_section": True})),
            (template_id, 'section', None, 2, 2, '2 тормозная позиция', 'ПЗ-2ТП', 3, json.dumps({})),
            
            # Парковая часть
            (template_id, 'section', None, 3, None, 'Бесстрелочный участок', 'ПП-БУ', 1, json.dumps({"has_train_filling": True})),
            (template_id, 'section', None, 3, None, '3 тормозная позиция', 'ПП-3ТП', 2, json.dumps({})),
            (template_id, 'section', None, 3, None, '4 тормозная позиция', 'ПП-4ТП', 3, json.dumps({})),
        ]
        
        for elem in elements:
            cursor.execute("""
                INSERT INTO template_elements (
                    template_id, element_type, parent_id, section_type_id, zone_type_id, 
                    name, code, sort_order, params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, elem)
        
        # Добавляем пути парка (201-232)
        for i in range(201, 233):
            cursor.execute("""
                INSERT INTO template_elements (
                    template_id, element_type, parent_id, section_type_id, zone_type_id,
                    name, code, sort_order, params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (template_id, 'section', None, 3, None, f'Путь {i}', f'П-{i}', i, json.dumps({"length_m": 850, "has_track_circuit": True})))
        
        print(f"✅ Создан шаблон с ID {template_id}")
    
    # Создаём тестовую схему для СПСМ горка № 3
    cursor.execute("SELECT id FROM parks WHERE name = 'СПСМ горка № 3'")
    park_row = cursor.fetchone()
    
    if park_row:
        park_id = park_row[0]
        cursor.execute("SELECT COUNT(*) FROM park_schemes WHERE park_id = ?", (park_id,))
        if cursor.fetchone()[0] == 0:
            # Создаём схему на основе шаблона
            cursor.execute("SELECT id FROM park_templates WHERE is_default = 1")
            template_id = cursor.fetchone()[0]
            
            # Получаем элементы шаблона
            cursor.execute("""
                SELECT element_type, parent_id, section_type_id, zone_type_id, name, code, sort_order, params
                FROM template_elements WHERE template_id = ?
            """, (template_id,))
            elements = cursor.fetchall()
            
            scheme = {"name": "СПСМ горка № 3", "sections": []}
            for elem in elements:
                scheme["sections"].append({
                    "element_type": elem[0],
                    "parent_id": elem[1],
                    "section_type_id": elem[2],
                    "zone_type_id": elem[3],
                    "name": elem[4],
                    "code": elem[5],
                    "sort_order": elem[6],
                    "params": json.loads(elem[7]) if elem[7] else {}
                })
            
            cursor.execute("""
                INSERT INTO park_schemes (park_id, template_id, data, version, is_active)
                VALUES (?, ?, ?, 1, 1)
            """, (park_id, template_id, json.dumps(scheme, ensure_ascii=False)))
            
            print(f"✅ Создана схема для парка ID {park_id}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("📊 ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
    print("="*50)
    
    # Выводим статистику
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM section_types")
    print(f"   section_types: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM zone_types")
    print(f"   zone_types: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM park_templates")
    print(f"   park_templates: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM template_elements")
    print(f"   template_elements: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM park_schemes")
    print(f"   park_schemes: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    init_data()