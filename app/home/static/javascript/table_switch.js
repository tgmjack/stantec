

var table_type = "table_from_scratch";
const table_ids = ["table_from_scratch_wrapper", "AG_Grid_table_wrapper"];



function set_table_type(new_table_type) {
    table_type = new_table_type;
    for (const table_id of table_ids) {

        const table_element = document.getElementById(table_id);    
        
        if (table_id === table_type+"_wrapper") {
            table_element.style.display = "block";
        } else {
            table_element.style.display = "none";
        }
    }
}


