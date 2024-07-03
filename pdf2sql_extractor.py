import pdfplumber
import pandas as pd
import re
import sqlite3
import logging

# Setup logging to write to both terminal and file
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger()

# Create file handler which logs even debug messages
fh = logging.FileHandler('report.log')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(log_format))

# Add the handlers to the logger
logger.addHandler(fh)

def extract_tables_from_pdf(pdf_path):
    tables = []
    table_names = []
    current_table = []
    current_table_name = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text().split('\n')
            for line in page_text:
                # Skip footer lines
                if "©Daffodil International University" in line:
                    continue
                
                if line.startswith("Table") and "Table structure for table" in line:
                    if current_table:
                        tables.append(current_table)
                        table_names.append(current_table_name)
                        current_table = []
                    current_table_name = line.split("Table structure for table")[-1].strip().rstrip(':')
                elif line.lower().startswith(("column", "id")) and current_table_name:
                    current_table.append(line.split())
                elif current_table:
                    current_table.append(line.split())
    
    if current_table:
        tables.append(current_table)
        table_names.append(current_table_name)
    
    return tables, table_names


def merge_tables(table1, table2):
    # Merge tables directly as headers are not repeated in tables spanning multiple pages
    return table1 + table2


def clean_table_data(tables, table_names):
    cleaned_tables = []
    for table, table_name in zip(tables, table_names):
        current_table = {
            'name': table_name,
            'columns': [],
            'data': []
        }
        
        if table and table[0][0].lower() in ['column', 'id']:
            current_table['columns'] = table[0]
            current_table['data'] = table[1:]
        else:
            current_table['data'] = table
        
        cleaned_tables.append(current_table)
    
    return cleaned_tables



def write_tables_to_txt(cleaned_tables, output_file):
    with open(output_file, 'w') as f:
        for table in cleaned_tables:
            f.write(f"Table: {table['name']}\n")
            f.write("\t".join(table['columns']) + "\n")
            for row in table['data']:
                f.write("\t".join(str(cell) for cell in row) + "\n")
            f.write("\n")
    logging.info(f"Data written to {output_file}")

def generate_sqlite_schema(cleaned_tables):
    schema = []
    for table in cleaned_tables:
        table_name = table['name'] or "unknown_table"
        table_name = re.sub(r'\s+', '_', table_name)
        if not table_name:
            continue
        create_table = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        columns = []
        for column in table['data']:
            if len(column) < 2:
                continue  # Skip rows with insufficient data
            col_name = re.sub(r'\s+', '_', column[0])
            col_type = map_to_sqlite_type(column[1] if len(column) > 1 else '')
            null = 'NOT NULL' if len(column) > 2 and column[2].lower() == 'no' else ''
            default = f"DEFAULT '{column[3]}'" if len(column) > 3 and column[3].lower() != 'null' else ''
            
            column_def = f"    {col_name} {col_type} {null} {default}".strip()
            columns.append(column_def)
        create_table += ",\n".join(columns) + "\n);"
        schema.append(create_table)
    return "\n\n".join(schema)

def map_to_sqlite_type(mysql_type):
    type_mapping = {
        'int': 'INTEGER',
        'varchar': 'TEXT',
        'text': 'TEXT',
        'timestamp': 'DATETIME',
        'float': 'REAL',
        'tinyint': 'INTEGER',
        'date': 'DATE'
    }
    for mysql, sqlite in type_mapping.items():
        if mysql in mysql_type.lower():
            return sqlite
    return 'TEXT'  # Default to TEXT if no match found

def write_sqlite_schema(schema, output_file):
    with open(output_file, 'w') as f:
        f.write(schema)
    logging.info(f"Schema written to {output_file}")

def main():
    pdf_path = 'ERD_Extracted_Table.pdf'
    txt_output = 'crm_database_tables.txt'
    sql_output = 'crm_database_schema.sql'
    csv_output = 'crm_database_schema.csv'
    
    tables, table_names = extract_tables_from_pdf(pdf_path)
    logging.info(f"Extracted {len(tables)} tables")
    
    cleaned_tables = clean_table_data(tables, table_names)
    logging.info(f"Cleaned {len(cleaned_tables)} tables")
    
    for table in cleaned_tables:
        logging.info(f"\nTable: {table['name']}")
        logging.info(f"Columns: {table['columns']}")
        logging.info(f"Data rows: {len(table['data'])}")
        logging.info("First few rows of data:")
        for row in table['data'][:3]:  # Print first 3 rows
            logging.info(row)
    
    write_tables_to_txt(cleaned_tables, txt_output)
    
    sqlite_schema = generate_sqlite_schema(cleaned_tables)
    write_sqlite_schema(sqlite_schema, sql_output)
    
    # Initialize a list to collect rows
    rows_list = []
    for table in cleaned_tables:
        table_name = table['name']
        for row in table['data']:
            # Append each row as a dictionary to the list, handling potential missing values
            rows_list.append({
                'Table': table_name,
                'Column': row[0] if len(row) > 0 else '',
                'Type': row[1] if len(row) > 1 else '',
                'Null': row[2] if len(row) > 2 else '',
                'Default': row[3] if len(row) > 3 else ''
            })
    
    # Create the DataFrame from the list of dictionaries
    df = pd.DataFrame(rows_list, columns=['Table', 'Column', 'Type', 'Null', 'Default'])
    logging.info("\nDataFrame Info:")
    logging.info(df.info())
    logging.info("\nFirst few rows of DataFrame:")
    logging.info(df.head())
    df.to_csv(csv_output, index=False)

    logging.info(f"\nSummary:")
    logging.info(f"- Extracted {len(tables)} tables from PDF")
    logging.info(f"- Cleaned and processed {len(cleaned_tables)} tables")
    logging.info(f"- Generated {len(rows_list)} rows of data")
    logging.info(f"- Output files: {txt_output}, {sql_output}, {csv_output}")

if __name__ == "__main__":
    main()
