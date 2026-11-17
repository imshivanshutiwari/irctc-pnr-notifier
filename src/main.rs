//! main.rs - Entry point for RailPulse (Rust Edition).

pub mod cadence;
pub mod notifier;
pub mod pnr_client;
pub mod stations;
pub mod tracker;
pub mod web_server;

#[cfg(test)]
mod tests;

use clap::{Parser, Subcommand};
use dotenvy::dotenv;
use std::path::PathBuf;
use tracing::info;
use tracing_subscriber::EnvFilter;

#[derive(Parser)]
#[command(name = "railpulse", author = "Shivanshu Tiwari", version = "1.0.0")]
#[command(about = "High-performance autonomous IRCTC PNR monitor & web dashboard in Rust")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    /// Specific PNR to track directly via CLI
    #[arg(long)]
    pnr: Option<String>,

    /// Path to JSON state file
    #[arg(long, default_value = "status_state.json")]
    state_file: PathBuf,

    /// Run in dry-run simulation mode (no external notifications sent)
    #[arg(long)]
    dry_run: bool,

    /// Send alerts immediately on first run baseline
    #[arg(long)]
    alert_on_first_run: bool,

    /// Gracefully continue without exit failure on temporary network/upstream errors
    #[arg(long)]
    allow_transient_errors: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Start the web dashboard and REST API server
    Server {
        #[arg(long, default_value_t = 8000)]
        port: u16,
        #[arg(long, default_value = "status_state.json")]
        state_file: PathBuf,
    },
    /// Check PNRs once and exit
    Check {
        #[arg(long)]
        pnr: Option<String>,
        #[arg(long, default_value = "status_state.json")]
        state_file: PathBuf,
        #[arg(long)]
        dry_run: bool,
        #[arg(long)]
        alert_on_first_run: bool,
        #[arg(long)]
        allow_transient_errors: bool,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let _ = dotenv();

    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .init();

    let cli = Cli::parse();

    match cli.command {
        Some(Commands::Server { port, state_file }) => {
            web_server::run_server(port, state_file).await?;
        }
        Some(Commands::Check {
            pnr,
            state_file,
            dry_run,
            alert_on_first_run,
            allow_transient_errors,
        }) => {
            run_cli_check(pnr, state_file, dry_run, alert_on_first_run, allow_transient_errors).await?;
        }
        None => {
            if cli.pnr.is_some() || std::env::var("PNR_NUMBER").is_ok() {
                run_cli_check(
                    cli.pnr,
                    cli.state_file,
                    cli.dry_run,
                    cli.alert_on_first_run,
                    cli.allow_transient_errors,
                )
                .await?;
            } else {
                // Default action: launch server
                web_server::run_server(8000, cli.state_file).await?;
            }
        }
    }

    Ok(())
}

async fn run_cli_check(
    pnr: Option<String>,
    state_file: PathBuf,
    dry_run: bool,
    alert_on_first_run: bool,
    allow_transient_errors: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let env_pnrs = std::env::var("PNR_NUMBER").ok();
    let pnr_target = pnr.or(env_pnrs);

    let notifier = notifier::Notifier::new(None, None, None, None, None, Some(dry_run));
    let tracker = tracker::PNRTracker::new(
        None,
        pnr_target.as_deref(),
        None,
        Some(notifier),
        Some(&state_file),
        None,
        alert_on_first_run,
    )
    .map_err(|e| Box::<dyn std::error::Error>::from(e))?;

    info!("[Tracker] Checking configured PNRs: {:?}", tracker.pnrs);
    let changed = tracker.check_all_pnrs(allow_transient_errors).await
        .map_err(|e| Box::<dyn std::error::Error>::from(e))?;

    if changed {
        info!("[Tracker] State changes detected and recorded.");
    } else {
        info!("[Tracker] No state changes detected.");
    }

    Ok(())
}
