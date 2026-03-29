import os
import glob
import json

# Ensure we run from the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def load_kanji_dict(paths):
    kanji_dict = {}
    for p in paths:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Format: [["亜","a á","","",["[á] thứ hai","[á] châu Á"]...]]
            for entry in data:
                kanji_char = entry[0]
                hanviet_reading = entry[1]
                kanji_dict[kanji_char] = hanviet_reading
    return kanji_dict

def process_markdown_file(filepath, kanji_dict):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    
    if not lines or lines[0] != '---':
        return # Not a standard frontmatter file
        
    in_frontmatter = True
    frontmatter = [lines[0]]
    body = []
    
    closing_dash_index = -1
    for i in range(1, len(lines)):
        if in_frontmatter and lines[i] == '---':
            closing_dash_index = i
            in_frontmatter = False
            continue
            
        if in_frontmatter:
            frontmatter.append(lines[i])
        else:
            body.append(lines[i])
            
    if closing_dash_index == -1:
        return # Malformed
        
    # check if hanviet already exists
    has_hanviet = False
    kanji_char = None
    
    for line in frontmatter:
        if line.startswith('kanji: '):
            kanji_char = line.split('kanji:', 1)[1].strip()
        if line.startswith('hanviet: '):
            has_hanviet = True
            
    if has_hanviet:
        # Already processed, or maybe we want to update it. Let's just update it.
        # Actually it's easier to remove old hanviet and re-add.
        frontmatter = [line for line in frontmatter if not line.startswith('hanviet: ')]

    if kanji_char:
        # Remove quotes if they exist
        if kanji_char.startswith(('"', "'")) and kanji_char.endswith(('"', "'")):
            kanji_char = kanji_char[1:-1]
            
        reading = kanji_dict.get(kanji_char, '')
        frontmatter.append(f'hanviet: "{reading}"')
            
    frontmatter.append('---')
    
    new_content = '\n'.join(frontmatter) + '\n' + '\n'.join(body) + '\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    os.chdir(PROJECT_ROOT)
    
    dict_paths = [
        'KanjiDictVN/out_vn/kanji_bank_1.json',
        'KanjiDictVN/out_vn/kanji_bank_2.json'
    ]
    
    print("Loading dictionary...")
    kanji_dict = load_kanji_dict(dict_paths)
    print(f"Loaded {len(kanji_dict)} kanji entries.")
    
    md_files = glob.glob('rtk1-v6/*.md') + glob.glob('rtk3-remain/*.md')
    print(f"Found {len(md_files)} markdown files.")
    
    processed = 0
    for file in md_files:
        process_markdown_file(file, kanji_dict)
        processed += 1
        
    print(f"Processed {processed} files.")

if __name__ == '__main__':
    main()
