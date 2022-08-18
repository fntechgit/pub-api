create table public.summit_entity_updates (
  id                  bigint generated by default as identity primary key,
  created_at 	      timestamp without time zone default timezone('utc'::text, now()) not null,
  summit_id 	      bigint not null,
  entity_id 	      bigint not null,
  entity_type  		  text  not null,
  entity_op 	  	  text not null
);

create index IDX_ENTITY_UPDATES_SUMMIT_ENTITY on public.summit_entity_updates (summit_id, entity_id, entity_type);

alter table public.summit_entity_updates replica identity full;

alter publication supabase_realtime add table public.summit_entity_updates;