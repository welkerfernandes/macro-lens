use std::io::{self, Read};

#[derive(Debug)]
struct Trend { slope: f64, r_squared: f64 }

fn fit(points: &[(i32, f64)]) -> Result<Trend, String> {
    if points.len() < 3 || points.iter().any(|(_, y)| !y.is_finite()) { return Err("Invalid observations".into()); }
    let mut years: Vec<_> = points.iter().map(|(x,_)| *x).collect();
    years.sort(); years.dedup();
    if years.len() != points.len() { return Err("Duplicate years".into()); }
    let n=points.len() as f64;
    let xm=points.iter().map(|(x,_)| *x as f64).sum::<f64>()/n;
    let ym=points.iter().map(|(_,y)| y).sum::<f64>()/n;
    let variance=points.iter().map(|(x,_)| (*x as f64-xm).powi(2)).sum::<f64>();
    if variance==0.0 { return Err("Zero year variance".into()); }
    let slope=points.iter().map(|(x,y)| (*x as f64-xm)*(y-ym)).sum::<f64>()/variance;
    let total=points.iter().map(|(_,y)| (y-ym).powi(2)).sum::<f64>();
    let residual=points.iter().map(|(x,y)| (y-(ym+slope*(*x as f64-xm))).powi(2)).sum::<f64>();
    let r_squared=if total==0.0 {1.0} else {1.0-residual/total};
    Ok(Trend{slope,r_squared})
}
fn parse(input: &str) -> Result<Vec<(i32,f64)>, String> {
    if input.len()>65536 { return Err("Input too large".into()); }
    input.lines().map(|line| {
        let (year,value)=line.split_once('\t').ok_or("Expected year TAB value")?;
        let year=year.parse::<i32>().map_err(|_| "Invalid year")?;
        let value=value.parse::<f64>().map_err(|_| "Invalid value")?;
        Ok((year,value))
    }).collect()
}
fn run() -> Result<(),String> {
    let mut input=String::new();
    io::stdin().take(65537).read_to_string(&mut input).map_err(|e| e.to_string())?;
    let trend=fit(&parse(&input)?)?;
    println!("{{\"slope_per_year\":{},\"r_squared\":{},\"engine\":\"rust\"}}",trend.slope,trend.r_squared);
    Ok(())
}
fn main(){if let Err(error)=run(){eprintln!("{}",error);std::process::exit(1)}}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn exact_line(){let r=fit(&[(2020,10.0),(2022,14.0),(2023,16.0)]).unwrap();assert!((r.slope-2.0).abs()<1e-12);assert!((r.r_squared-1.0).abs()<1e-12);}
    #[test] fn constant(){assert_eq!(fit(&[(2020,5.0),(2021,5.0),(2022,5.0)]).unwrap().slope,0.0);}
    #[test] fn duplicate_rejected(){assert!(fit(&[(2020,1.0),(2020,2.0),(2022,3.0)]).is_err());}
    #[test] fn nonfinite_rejected(){assert!(fit(&[(2020,f64::NAN),(2021,2.0),(2022,3.0)]).is_err());}
    #[test] fn parse_rejected(){assert!(parse("bad data").is_err());}
}
