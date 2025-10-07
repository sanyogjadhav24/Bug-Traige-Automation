import React, { useState } from "react";
import {
  Container,
  Typography,
  TextField,
  Button,
  Box,
  Paper,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Avatar,
  LinearProgress,
  Stack,
} from "@mui/material";
import axios from "axios";

// Severity color mapping
const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case "critical": return "#f44336";
    case "high": return "#ff9800";
    case "major": return "#ff9800";
    case "medium": return "#2196f3";
    case "low": return "#4caf50";
    case "minor": return "#4caf50";
    default: return "#9e9e9e";
  }
};

// Category color mapping
const getCategoryColor = (category) => {
  switch (category?.toLowerCase()) {
    case "bug": return "#f44336";
    case "task": return "#2196f3";
    case "improvement": return "#4caf50";
    default: return "#9e9e9e";
  }
};

// Get initials from email
const getInitials = (email) => {
  if (!email) return "?";
  const parts = email.split("@")[0].split(".");
  return parts.map(p => p.charAt(0).toUpperCase()).join("").slice(0, 2);
};

function App() {
  const [project, setProject] = useState("DEM");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jiraLoading, setJiraLoading] = useState(false);
  const [jiraResult, setJiraResult] = useState(null);

  const handlePredict = async () => {
    setLoading(true);
    setJiraResult(null);
    try {
      const res = await axios.post("http://127.0.0.1:8000/predict", {
        project,
        summary,
        description,
      });
      setResult(res.data);
    } catch (err) {
      setResult({ error: "Prediction failed. Please check if the API server is running." });
    }
    setLoading(false);
  };

  const handleCreateJira = async () => {
    setJiraLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:8000/create_jira", {
        project,
        summary,
        description,
        category: result.category,
        severity: result.severity,
        assignee: result.assignee_top1,
      });
      setJiraResult(res.data);
    } catch (err) {
      setJiraResult({ error: "Jira creation failed." });
    }
    setJiraLoading(false);
  };

  return (
    <Box sx={{ bgcolor: "#f5f7fa", minHeight: "100vh", py: 4 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: "primary.main", color: "white", borderRadius: 2 }}>
          <Typography variant="h3" gutterBottom sx={{ fontWeight: "bold" }}>
            🎯 Bug Triage Automation Dashboard
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            Intelligent issue classification using Machine Learning & NLP
          </Typography>
        </Paper>

        <Grid container spacing={3}>
          {/* Input Section */}
          <Grid item xs={12} md={6}>
            <Card elevation={2} sx={{ borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ fontWeight: "bold", color: "primary.main" }}>
                  📝 Issue Details
                </Typography>
                <Divider sx={{ mb: 3 }} />

                <Stack spacing={3}>
                  <TextField
                    label="Project"
                    fullWidth
                    value={project}
                    onChange={(e) => setProject(e.target.value)}
                    variant="outlined"
                    sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
                  />
                  <TextField
                    label="Summary"
                    fullWidth
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    variant="outlined"
                    placeholder="Brief description of the issue..."
                    sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
                  />
                  <TextField
                    label="Description"
                    fullWidth
                    multiline
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    variant="outlined"
                    placeholder="Detailed description of the issue, steps to reproduce, expected vs actual behavior..."
                    sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
                  />

                  <Button
                    variant="contained"
                    fullWidth
                    size="large"
                    onClick={handlePredict}
                    disabled={loading || !summary.trim() || !description.trim()}
                    sx={{ 
                      py: 1.5, 
                      borderRadius: 2, 
                      fontSize: "1.1rem",
                      fontWeight: "bold",
                      boxShadow: 2
                    }}
                  >
                    {loading ? (
                      <>
                        <CircularProgress size={24} sx={{ mr: 1, color: "white" }} />
                        Analyzing Issue...
                      </>
                    ) : (
                      "🔍 Analyze & Predict"
                    )}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Results Section */}
          <Grid item xs={12} md={6}>
            {result ? (
              <Stack spacing={2}>
                {/* Error Handling */}
                {result.error ? (
                  <Alert severity="error" sx={{ borderRadius: 2 }}>
                    <Typography variant="h6">❌ Error</Typography>
                    {result.error}
                  </Alert>
                ) : (
                  <>
                    {/* Prediction Results */}
                    <Card elevation={2} sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ p: 3 }}>
                        <Typography variant="h5" gutterBottom sx={{ fontWeight: "bold", color: "success.main" }}>
                          🎯 AI Predictions
                        </Typography>
                        <Divider sx={{ mb: 3 }} />

                        <Grid container spacing={2}>
                          {/* Category */}
                          <Grid item xs={12} sm={6}>
                            <Box sx={{ textAlign: "center", p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                CATEGORY
                              </Typography>
                              <Chip
                                label={result.category}
                                sx={{
                                  bgcolor: getCategoryColor(result.category),
                                  color: "white",
                                  fontWeight: "bold",
                                  fontSize: "1rem",
                                  px: 2,
                                  py: 1
                                }}
                              />
                              <Box sx={{ mt: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={result.category_conf * 100}
                                  sx={{ 
                                    height: 8, 
                                    borderRadius: 1,
                                    bgcolor: "grey.200",
                                    "& .MuiLinearProgress-bar": {
                                      bgcolor: getCategoryColor(result.category)
                                    }
                                  }}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  Confidence: {(result.category_conf * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                            </Box>
                          </Grid>

                          {/* Severity */}
                          <Grid item xs={12} sm={6}>
                            <Box sx={{ textAlign: "center", p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                SEVERITY
                              </Typography>
                              <Chip
                                label={result.severity}
                                sx={{
                                  bgcolor: getSeverityColor(result.severity),
                                  color: "white",
                                  fontWeight: "bold",
                                  fontSize: "1rem",
                                  px: 2,
                                  py: 1
                                }}
                              />
                              <Box sx={{ mt: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={result.severity_conf * 100}
                                  sx={{ 
                                    height: 8, 
                                    borderRadius: 1,
                                    bgcolor: "grey.200",
                                    "& .MuiLinearProgress-bar": {
                                      bgcolor: getSeverityColor(result.severity)
                                    }
                                  }}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  Confidence: {(result.severity_conf * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                            </Box>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>

                    {/* Assignee Section */}
                    <Card elevation={2} sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom sx={{ fontWeight: "bold", color: "info.main" }}>
                          👥 Recommended Assignees
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        {/* Primary Assignee */}
                        <Box sx={{ p: 2, bgcolor: "primary.50", borderRadius: 2, mb: 2 }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                            <Avatar sx={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                              {getInitials(result.assignee_top1)}
                            </Avatar>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                                Primary Recommendation
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {result.assignee_top1}
                              </Typography>
                            </Box>
                            <Chip label="BEST MATCH" color="primary" sx={{ fontWeight: "bold" }} />
                          </Box>
                        </Box>

                        {/* Alternative Assignees */}
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Alternative Options:
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {result.assignee_top3?.slice(1).map((assignee, index) => (
                            <Box key={index} sx={{ display: "flex", alignItems: "center", gap: 1, p: 1, bgcolor: "grey.50", borderRadius: 1 }}>
                              <Avatar sx={{ bgcolor: "grey.400", width: 24, height: 24, fontSize: "0.75rem" }}>
                                {getInitials(assignee)}
                              </Avatar>
                              <Typography variant="caption">{assignee}</Typography>
                            </Box>
                          ))}
                        </Stack>
                      </CardContent>
                    </Card>

                    {/* Jira Integration */}
                    {result.jira_suggested && (
                      <Card elevation={2} sx={{ borderRadius: 2, bgcolor: "warning.50" }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ fontWeight: "bold", color: "warning.main" }}>
                            🎫 Jira Integration
                          </Typography>
                          <Divider sx={{ mb: 2 }} />
                          
                          <Alert severity="info" sx={{ mb: 2, borderRadius: 2 }}>
                            Ready to create Jira issue with the predicted category, severity, and assignee.
                          </Alert>

                          <Button
                            variant="contained"
                            color="warning"
                            fullWidth
                            size="large"
                            onClick={handleCreateJira}
                            disabled={jiraLoading}
                            sx={{ 
                              py: 1.5, 
                              borderRadius: 2, 
                              fontSize: "1.1rem",
                              fontWeight: "bold",
                              boxShadow: 2
                            }}
                          >
                            {jiraLoading ? (
                              <>
                                <CircularProgress size={24} sx={{ mr: 1, color: "white" }} />
                                Creating Issue...
                              </>
                            ) : (
                              "🚀 Create Jira Issue"
                            )}
                          </Button>

                          {jiraResult && (
                            <Box sx={{ mt: 2 }}>
                              {jiraResult.success ? (
                                <Alert severity="success" sx={{ borderRadius: 2 }}>
                                  <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                                    ✅ Jira Issue Created Successfully!
                                  </Typography>
                                  <Typography variant="body2">
                                    Issue Key: <strong>{jiraResult.issue_key}</strong>
                                  </Typography>
                                </Alert>
                              ) : (
                                <Alert severity="error" sx={{ borderRadius: 2 }}>
                                  <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                                    ❌ Failed to Create Jira Issue
                                  </Typography>
                                  <Typography variant="body2">
                                    {jiraResult.error || "Unknown error occurred"}
                                  </Typography>
                                </Alert>
                              )}
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    {/* Model Info */}
                    {/* <Card elevation={1} sx={{ borderRadius: 2, bgcolor: "grey.50" }}>
                      <CardContent sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                          🤖 Model Version: {result.model_version} | 
                          🧠 Powered by ML & NLP | 
                          📊 Prediction completed
                        </Typography>
                      </CardContent>
                    </Card> */}
                  </>
                )}
              </Stack>
            ) : (
              <Card elevation={2} sx={{ borderRadius: 2, height: "fit-content" }}>
                <CardContent sx={{ p: 4, textAlign: "center" }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    🔍 Ready for Analysis
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Enter issue details on the left and click "Analyze & Predict" to get AI-powered
                    category, severity, and assignee recommendations.
                  </Typography>
                  <Box sx={{ mt: 3, display: "flex", justifyContent: "center", gap: 2 }}>
                    <Chip label="Machine Learning" variant="outlined" />
                    <Chip label="NLP Analysis" variant="outlined" />
                    <Chip label="Auto-Assignment" variant="outlined" />
                  </Box>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>

        {/* Footer */}
        <Box sx={{ mt: 4, textAlign: "center" }}>
          <Typography variant="body2" color="text.secondary">
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default App;